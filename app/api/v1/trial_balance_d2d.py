"""Trial Balance Date to Date report API."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_any_permission
from app.config.settings import settings
from app.database.business_session import get_business_db
from app.database.session import get_db
from app.repositories.audit_repository import AuditRepository
from app.reports.trial_balance_d2d_pdf import render_trial_balance_d2d_pdf
from app.schemas.gl_ledger_report import (
    GlAccountLookup,
    GlLedgerEmailResponse,
    GlLedgerEmailStatus,
    GlLedgerMobilePdfResponse,
    GlLedgerWhatsAppResponse,
    GlLedgerWhatsAppStatus,
    GlWhatsAppContactLookup,
)
from app.schemas.trial_balance_d2d import (
    TrialBalanceD2DData,
    TrialBalanceD2DEmailRequest,
    TrialBalanceD2DRequest,
    TrialBalanceD2DWhatsAppRequest,
)
from app.services.email_service import EmailDeliveryError, EmailNotConfiguredError, EmailService
from app.services.gl_ledger_report_service import GlLedgerReportService
from app.services.pdf_view_token_store import get_pdf, store_pdf
from app.services.trial_balance_d2d_service import TrialBalanceD2DService
from app.services.whatsapp_service import (
    WhatsAppDeliveryError,
    WhatsAppNotConfiguredError,
    WhatsAppService,
    normalize_pk_phone,
)
from app.utils import get_client_ip

router = APIRouter()

_VIEW_PERMS = require_any_permission(
    "reports.gl_ledger.view",
    "inventory.fin_item.view",
    "auth.admin.full",
)


def _build_pdf(params: TrialBalanceD2DRequest, db: Session) -> tuple[bytes, str, TrialBalanceD2DData]:
    report = TrialBalanceD2DService(db).build_report(params)
    pdf_bytes = render_trial_balance_d2d_pdf(report)
    suffix = "short" if params.short_format else "full"
    filename = f"trial-balance-d2d-{suffix}-{params.date_from}-{params.date_to}.pdf"
    return pdf_bytes, filename, report


def _pdf_response(params: TrialBalanceD2DRequest, *, inline: bool, db: Session) -> Response:
    pdf_bytes, filename, _report = _build_pdf(params, db)
    disposition = "inline" if inline else "attachment"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@router.get("/accounts/search", response_model=list[GlAccountLookup])
def search_accounts(
    q: str = Query(..., min_length=1),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return GlLedgerReportService(db).search_accounts(q)


@router.get("/accounts/{ac_id}", response_model=GlAccountLookup)
def get_account(
    ac_id: int,
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return GlLedgerReportService(db).lookup_account(ac_id)


@router.get("/pdf")
def generate_pdf_get(
    start_ac_id: int = Query(..., ge=1),
    end_ac_id: int = Query(..., ge=1),
    date_from: date = Query(...),
    date_to: date = Query(...),
    suppress_zero_bal: bool = Query(False),
    complete_report: bool = Query(False),
    short_format: bool = Query(False),
    sort_by: Literal["ac_id", "ac_title"] = Query("ac_id"),
    sort_order: Literal["asc", "desc"] = Query("asc"),
    inline: bool = Query(True),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    params = TrialBalanceD2DRequest(
        start_ac_id=start_ac_id,
        end_ac_id=end_ac_id,
        date_from=date_from,
        date_to=date_to,
        suppress_zero_bal=suppress_zero_bal,
        complete_report=complete_report,
        short_format=short_format,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return _pdf_response(params, inline=inline, db=db)


@router.post("/pdf")
def generate_pdf(
    params: TrialBalanceD2DRequest,
    inline: bool = Query(False),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return _pdf_response(params, inline=inline, db=db)


@router.post("/email", response_model=GlLedgerEmailResponse)
def email_pdf(
    params: TrialBalanceD2DEmailRequest,
    current_user: CurrentUser = Depends(_VIEW_PERMS),
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
        f"Trial Balance Date to Date {params.date_from.strftime('%d/%m/%Y')} - "
        f"{params.date_to.strftime('%d/%m/%Y')}"
    )
    body_lines = [
        "Please find the Trial Balance Date to Date report attached.",
        "",
        f"Company: {report.company_name}",
        f"Criteria: {report.criteria}",
        f"Accounts listed: {report.total_rows}",
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


@router.post("/pdf/mobile", response_model=GlLedgerMobilePdfResponse)
def create_mobile_pdf_link(
    params: TrialBalanceD2DRequest,
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    pdf_bytes, filename, _report = _build_pdf(params, db)
    token = store_pdf(pdf_bytes, filename, ttl_minutes=15)
    base = settings.base_url.rstrip("/")
    view_url = f"{base}{settings.api_v1_prefix}/reports/trial-balance-d2d/pdf/mobile/{token}"
    return GlLedgerMobilePdfResponse(view_url=view_url, filename=filename, expires_in_minutes=15)


@router.get("/pdf/mobile/{token}")
def view_mobile_pdf(token: str):
    result = get_pdf(token)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF link expired or not found.")
    pdf_bytes, filename = result
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/email/status", response_model=GlLedgerEmailStatus)
def email_status(_user: CurrentUser = Depends(_VIEW_PERMS)):
    service = EmailService()
    from_email = settings.smtp_from_email.strip() or settings.smtp_user.strip()
    return GlLedgerEmailStatus(
        configured=service.is_configured(),
        from_email=from_email,
        hint=service.configuration_hint(),
    )


@router.get("/whatsapp/contacts/search", response_model=list[GlWhatsAppContactLookup])
def search_whatsapp_contacts(
    q: str = Query(..., min_length=1),
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return GlLedgerReportService(db).search_whatsapp_contacts(q)


@router.get("/whatsapp/contacts/lookup/{ac_id}", response_model=GlWhatsAppContactLookup)
def lookup_whatsapp_contact(
    ac_id: int,
    _user: CurrentUser = Depends(_VIEW_PERMS),
    db: Session = Depends(get_business_db),
):
    return GlLedgerReportService(db).lookup_whatsapp_contact(ac_id)


@router.get("/whatsapp/status", response_model=GlLedgerWhatsAppStatus)
def whatsapp_status(_user: CurrentUser = Depends(_VIEW_PERMS)):
    service = WhatsAppService()
    return GlLedgerWhatsAppStatus(
        configured=service.is_configured(),
        hint=service.configuration_hint(),
    )


@router.post("/whatsapp", response_model=GlLedgerWhatsAppResponse)
def send_whatsapp_pdf(
    request: Request,
    params: TrialBalanceD2DWhatsAppRequest,
    current_user: CurrentUser = Depends(_VIEW_PERMS),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    wa_service = WhatsAppService()
    phone = normalize_pk_phone(params.to_phone)
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid WhatsApp number. Use e.g. 03001234567 or 3001234567.",
        )

    try:
        pdf_bytes, filename, report = _build_pdf(params, business_db)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate report PDF: {exc}",
        ) from exc

    token = store_pdf(pdf_bytes, filename, ttl_minutes=30)
    base = settings.base_url.rstrip("/")
    document_url = f"{base}{settings.api_v1_prefix}/reports/trial-balance-d2d/pdf/mobile/{token}"

    caption_lines = [
        report.company_name,
        report.report_title,
        report.date_range,
        f"Accounts listed: {report.total_rows}",
    ]
    if params.message:
        caption_lines.extend(["", params.message])
    caption = "\n".join(caption_lines)

    try:
        wa_service.send_document(
            phone,
            document_url,
            filename=filename,
            caption=caption,
        )
    except WhatsAppNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except WhatsAppDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    AuditRepository(auth_db).log_audit(
        action="TB_D2D_WHATSAPP_SEND",
        user_id=current_user.user_id,
        username=current_user.username,
        entity_type="TRIAL_BALANCE_D2D",
        ip_address=get_client_ip(request),
        status="SUCCESS",
        new_values=f"to={phone}; file={filename}",
    )
    auth_db.commit()

    display_phone = f"+{phone}"
    return GlLedgerWhatsAppResponse(
        message=f"PDF sent to WhatsApp {display_phone}.",
        to_phone=display_phone,
    )
