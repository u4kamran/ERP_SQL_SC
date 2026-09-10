"""General Ledger report API."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_any_permission, require_report_delivery
from app.config.settings import settings
from app.database.business_session import get_business_db
from app.database.session import get_db
from app.repositories.audit_repository import AuditRepository
from app.reports.gl_ledger_pdf import render_gl_ledger_pdf
from app.schemas.gl_ledger_report import (
    GlAccountLookup,
    GlLedgerEmailRequest,
    GlLedgerEmailResponse,
    GlLedgerEmailStatus,
    GlLedgerMobilePdfResponse,
    GlLedgerReportData,
    GlLedgerReportRequest,
    GlLedgerWhatsAppRequest,
    GlLedgerWhatsAppResponse,
    GlLedgerWhatsAppStatus,
    GlWhatsAppContactLookup,
)
from app.services.email_service import EmailDeliveryError, EmailNotConfiguredError, EmailService
from app.services.gl_ledger_report_service import GlLedgerReportService
from app.services.pdf_view_token_store import get_pdf, store_pdf
from app.services.whatsapp_service import (
    WhatsAppDeliveryError,
    WhatsAppNotConfiguredError,
    WhatsAppService,
    normalize_pk_phone,
)
from app.utils import get_client_ip

router = APIRouter()

_LEGACY = ("inventory.fin_item.view", "auth.admin.full")
_GL_VIEW = ("reports.gl_ledger.view", "reports.gl_ledger_mobile.view", *_LEGACY)
_GL_LEDGER_PERMS = require_any_permission(*_GL_VIEW)
_GL_EMAIL_PERMS = require_report_delivery(
    *_GL_VIEW,
    action_permissions=("reports.gl_ledger.email", "reports.gl_ledger_mobile.email"),
    denied_detail="You do not have permission to email this report.",
)
_GL_WHATSAPP_PERMS = require_report_delivery(
    *_GL_VIEW,
    action_permissions=("reports.gl_ledger.whatsapp", "reports.gl_ledger_mobile.whatsapp"),
    denied_detail="You do not have permission to send this report through WhatsApp.",
)


def _build_pdf(params: GlLedgerReportRequest, db: Session) -> tuple[bytes, str, GlLedgerReportData]:
    report = GlLedgerReportService(db).build_report(params)
    pdf_bytes = render_gl_ledger_pdf(report)
    filename = f"gl-ledger-{params.date_from}-{params.date_to}.pdf"
    return pdf_bytes, filename, report


def _pdf_response(params: GlLedgerReportRequest, *, inline: bool, db: Session) -> Response:
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
    current_user: CurrentUser = Depends(_GL_LEDGER_PERMS),
    db: Session = Depends(get_business_db),
):
    return GlLedgerReportService(db).search_accounts(q)


@router.get("/accounts/{ac_id}", response_model=GlAccountLookup)
def get_account(
    ac_id: int,
    current_user: CurrentUser = Depends(_GL_LEDGER_PERMS),
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
    page_wise: bool = Query(False),
    inline: bool = Query(True),
    current_user: CurrentUser = Depends(_GL_LEDGER_PERMS),
    db: Session = Depends(get_business_db),
):
    """Open PDF directly in browser — works on mobile (use inline=true)."""
    params = GlLedgerReportRequest(
        start_ac_id=start_ac_id,
        end_ac_id=end_ac_id,
        date_from=date_from,
        date_to=date_to,
        suppress_zero_bal=suppress_zero_bal,
        complete_report=complete_report,
        page_wise=page_wise,
    )
    return _pdf_response(params, inline=inline, db=db)


@router.post("/pdf")
def generate_pdf(
    params: GlLedgerReportRequest,
    inline: bool = Query(False),
    current_user: CurrentUser = Depends(_GL_LEDGER_PERMS),
    db: Session = Depends(get_business_db),
):
    return _pdf_response(params, inline=inline, db=db)


@router.post("/email", response_model=GlLedgerEmailResponse)
def email_pdf(
    params: GlLedgerEmailRequest,
    current_user: CurrentUser = Depends(_GL_EMAIL_PERMS),
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
        f"GL Ledger Report {params.date_from.strftime('%d/%m/%Y')} - "
        f"{params.date_to.strftime('%d/%m/%Y')}"
    )
    body_lines = [
        "Please find the General Ledger report attached.",
        "",
        f"Company: {report.company_name}",
        f"Criteria: {report.criteria}",
        f"Accounts listed: {report.total_accounts}",
        f"Generated by: {current_user.username}",
        f"Generated on: {report.printed_on}",
    ]
    if params.message:
        body_lines.extend(["", "Message:", params.message])
    body_lines.extend(["", f"This is an automated message from {settings.app_name}."])
    body_text = "\n".join(body_lines)

    email_service = EmailService()
    try:
        email_service.send_email(
            recipients,
            subject,
            body_text,
            attachment=(filename, pdf_bytes, "application/pdf"),
        )
    except EmailNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        message = str(exc)
        if "535" in message or "BadCredentials" in message:
            message = (
                "Gmail rejected the login. Use a Gmail App Password in SMTP_PASSWORD "
                "(not your normal Gmail password)."
            )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=message) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not send email: {exc}",
        ) from exc

    return GlLedgerEmailResponse(
        message=f"Report emailed to {', '.join(recipients)}.",
        recipients=recipients,
    )


@router.post("/pdf/mobile", response_model=GlLedgerMobilePdfResponse)
def create_mobile_pdf_link(
    params: GlLedgerReportRequest,
    current_user: CurrentUser = Depends(_GL_LEDGER_PERMS),
    db: Session = Depends(get_business_db),
):
    """Generate PDF and return a short-lived view link — works on mobile Safari/Chrome."""
    pdf_bytes, filename, _report = _build_pdf(params, db)
    token = store_pdf(pdf_bytes, filename, ttl_minutes=15)
    base = settings.base_url.rstrip("/")
    view_url = f"{base}{settings.api_v1_prefix}/reports/gl-ledger/pdf/mobile/{token}"
    return GlLedgerMobilePdfResponse(view_url=view_url, filename=filename, expires_in_minutes=15)


@router.get("/pdf/mobile/{token}")
def view_mobile_pdf(token: str):
    """Open PDF on mobile without Authorization header (token expires in 15 minutes)."""
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
def email_status(
    current_user: CurrentUser = Depends(_GL_EMAIL_PERMS),
):
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
    current_user: CurrentUser = Depends(_GL_WHATSAPP_PERMS),
    db: Session = Depends(get_business_db),
):
    return GlLedgerReportService(db).search_whatsapp_contacts(q)


@router.get("/whatsapp/contacts/lookup/{ac_id}", response_model=GlWhatsAppContactLookup)
def lookup_whatsapp_contact(
    ac_id: int,
    current_user: CurrentUser = Depends(_GL_WHATSAPP_PERMS),
    db: Session = Depends(get_business_db),
):
    return GlLedgerReportService(db).lookup_whatsapp_contact(ac_id)


@router.get("/whatsapp/status", response_model=GlLedgerWhatsAppStatus)
def whatsapp_status(
    current_user: CurrentUser = Depends(_GL_WHATSAPP_PERMS),
):
    service = WhatsAppService()
    return GlLedgerWhatsAppStatus(
        configured=service.is_configured(),
        hint=service.configuration_hint(),
    )


@router.post("/whatsapp", response_model=GlLedgerWhatsAppResponse)
def send_whatsapp_pdf(
    request: Request,
    params: GlLedgerWhatsAppRequest,
    current_user: CurrentUser = Depends(_GL_WHATSAPP_PERMS),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    """Generate PDF and send automatically to WhatsApp number via Meta Cloud API."""
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
    document_url = f"{base}{settings.api_v1_prefix}/reports/gl-ledger/pdf/mobile/{token}"

    caption_lines = [
        report.company_name,
        "GL Ledger Report",
        report.date_range,
        f"Accounts: {report.total_accounts}",
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
        action="GL_LEDGER_WHATSAPP_SEND",
        user_id=current_user.user_id,
        username=current_user.username,
        entity_type="GL_LEDGER",
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
