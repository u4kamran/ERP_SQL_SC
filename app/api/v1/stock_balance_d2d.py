"""Stock Balance Date to Date report API."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_any_permission, require_report_delivery
from app.config.settings import settings
from app.database.business_session import get_business_db
from app.reports.stock_balance_d2d_pdf import render_stock_balance_d2d_pdf
from app.schemas.gl_ledger_report import GlLedgerEmailResponse, GlLedgerEmailStatus
from app.schemas.stock_balance_d2d import (
    StockBalanceD2DData,
    StockBalanceD2DEmailRequest,
    StockBalanceD2DRequest,
    StockItemLookup,
)
from app.services.email_service import EmailDeliveryError, EmailNotConfiguredError, EmailService
from app.services.stock_balance_d2d_service import StockBalanceD2DService

router = APIRouter()

_LEGACY = ("inventory.fin_item.view", "auth.admin.full")
_STOCK_VIEW = (
    "reports.stock_balance_d2d.view",
    *_LEGACY,
)
_VIEW_PERMS = require_any_permission(*_STOCK_VIEW)
_EMAIL_PERMS = require_report_delivery(
    *_STOCK_VIEW,
    action_permissions=("reports.stock_balance_d2d.email",),
    denied_detail="You do not have permission to email this report.",
)


def _build_pdf(params: StockBalanceD2DRequest, db: Session) -> tuple[bytes, str, StockBalanceD2DData]:
    report = StockBalanceD2DService(db).build_report(params)
    pdf_bytes = render_stock_balance_d2d_pdf(report)
    filename = (
        f"Stock_Balance_{'Amt_' if params.print_amount else ''}"
        f"{params.date_from.strftime('%d-%m-%Y')}"
        f"_to_{params.date_to.strftime('%d-%m-%Y')}.pdf"
    )
    return pdf_bytes, filename, report


def _pdf_response(params: StockBalanceD2DRequest, *, inline: bool, db: Session) -> Response:
    pdf_bytes, filename, _report = _build_pdf(params, db)
    disposition = "inline" if inline else "attachment"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@router.get("/items/search", response_model=list[StockItemLookup])
def search_items(
    q: str = Query(..., min_length=1),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return StockBalanceD2DService(db).search_items(q)


@router.get("/items/{item_id}", response_model=StockItemLookup)
def get_item(
    item_id: int,
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return StockBalanceD2DService(db).lookup_item(item_id)


@router.get("/pdf")
def generate_pdf_get(
    start_item_id: int = Query(..., ge=1),
    end_item_id: int = Query(..., ge=1),
    date_from: date = Query(...),
    date_to: date = Query(...),
    suppress_zero_bal: bool = Query(False),
    complete_report: bool = Query(False),
    show_manual_id: bool = Query(True),
    store_ledger: bool = Query(False),
    print_amount: bool = Query(False),
    sort_by: Literal["ac_id", "ac_title"] = Query("ac_id"),
    sort_order: Literal["asc", "desc"] = Query("asc"),
    inline: bool = Query(True),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    params = StockBalanceD2DRequest(
        start_item_id=start_item_id,
        end_item_id=end_item_id,
        date_from=date_from,
        date_to=date_to,
        suppress_zero_bal=suppress_zero_bal,
        complete_report=complete_report,
        show_manual_id=show_manual_id,
        store_ledger=store_ledger,
        print_amount=print_amount,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return _pdf_response(params, inline=inline, db=db)


@router.post("/pdf")
def generate_pdf(
    params: StockBalanceD2DRequest,
    inline: bool = Query(False),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return _pdf_response(params, inline=inline, db=db)


@router.post("/email", response_model=GlLedgerEmailResponse)
def email_pdf(
    params: StockBalanceD2DEmailRequest,
    current_user: CurrentUser = Depends(_EMAIL_PERMS),
    db: Session = Depends(get_business_db),
):
    try:
        pdf_bytes, filename, report = _build_pdf(params, db)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate report PDF: {exc}",
        ) from exc

    recipients = [part.strip() for part in params.to_email.split(",") if part.strip()]
    subject = params.subject or (
        f"Stock Balance Date to Date {params.date_from.strftime('%d/%m/%Y')} - "
        f"{params.date_to.strftime('%d/%m/%Y')}"
    )
    body_lines = [
        "Please find the Stock Balance Date to Date report attached.",
        "",
        f"Company: {report.company_name}",
        f"Criteria: {report.criteria}",
        f"Items listed: {report.total_rows}",
        f"Generated by: {current_user.username}",
        f"Generated on: {report.printed_on}",
    ]
    if params.message:
        body_lines.extend(["", "Message:", params.message])
    body_lines.extend(["", f"This is an automated message from {settings.app_name}."])

    email_service = EmailService()
    try:
        email_service.send_email(
            recipients,
            subject,
            "\n".join(body_lines),
            attachment=(filename, pdf_bytes, "application/pdf"),
        )
    except EmailNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return GlLedgerEmailResponse(
        message=f"Report emailed to {', '.join(recipients)}.",
        recipients=recipients,
    )


@router.get("/email/status", response_model=GlLedgerEmailStatus)
def email_status(_user: CurrentUser = Depends(_EMAIL_PERMS)):
    service = EmailService()
    from_email = settings.smtp_from_email.strip() or settings.smtp_user.strip()
    return GlLedgerEmailStatus(
        configured=service.is_configured(),
        from_email=from_email,
        hint=service.configuration_hint(),
    )
