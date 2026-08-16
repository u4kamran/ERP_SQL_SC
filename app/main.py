"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import api_router
from app.config.settings import settings
from app.config.site_links import get_external_links, get_internal_link_groups
from app.logging.logger import logger
from app.middleware.security import csrf_middleware, security_headers_middleware
from app.middleware.menu_guard import menu_access_guard_middleware

from app.services.email_service import EmailService

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
templates.env.globals["base_url"] = settings.base_url.rstrip("/")
templates.env.globals["internal_link_groups"] = get_internal_link_groups()
templates.env.globals["external_links"] = get_external_links(settings.base_url)
templates.env.globals["smtp_configured"] = lambda: EmailService().is_configured()
templates.env.globals["smtp_hint"] = lambda: EmailService().configuration_hint()
templates.env.globals["company_name"] = settings.company_display_name
templates.env.globals["company_address"] = settings.company_address
templates.env.globals["brand_short"] = settings.brand_short_label
templates.env.globals["brand_tagline"] = settings.brand_tagline_label
templates.env.globals["brand_slogan"] = settings.brand_slogan
templates.env.globals["brand_logo_url"] = settings.brand_logo_url
templates.env.globals["brand_icon_url"] = settings.brand_icon_url
templates.env.globals["site_code"] = (settings.site_code or "erp").lower()
templates.env.globals["company_phone"] = settings.company_phone


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s [%s]", settings.app_name, settings.app_env)
    logger.info("In-process jobs (delivery sync / SMS email / dashboard email) are off in the web process.")
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=f"{settings.app_name} - Enterprise ERP",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

if settings.is_production and "*" not in settings.allowed_hosts_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(security_headers_middleware)
app.middleware("http")(csrf_middleware)
app.middleware("http")(menu_access_guard_middleware)

static_dir = BASE_DIR / "app" / "static"
static_dir.mkdir(parents=True, exist_ok=True)


class NoCacheStaticFiles(StaticFiles):
  async def get_response(self, path, scope):
    response = await super().get_response(path, scope)
    if not settings.is_production:
      response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


app.mount("/static", NoCacheStaticFiles(directory=str(static_dir)), name="static")

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")


@app.get("/guest/scan", response_class=HTMLResponse)
async def guest_price_scan_page(request: Request):
    return templates.TemplateResponse(
        request,
        "guest/price_scan.html",
        {"app_name": settings.app_name},
    )


@app.get("/guest/chat", response_class=HTMLResponse)
async def guest_chat_page(request: Request):
    from app.services.speech_to_text_service import SpeechToTextService

    stt = SpeechToTextService()
    return templates.TemplateResponse(
        request,
        "guest/chat.html",
        {
            "app_name": settings.app_name,
            "guest_mobile_otp_required": bool(settings.guest_mobile_otp_required),
            "guest_voice_cloud_enabled": stt.is_configured(),
            "guest_voice_provider": stt.provider_label(),
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "app_name": settings.app_name,
            "csrf_token": request.cookies.get(settings.csrf_cookie_name, ""),
        },
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "app_name": settings.app_name,
            "internal_link_groups": get_internal_link_groups(),
            "external_links": get_external_links(settings.base_url),
        },
    )


@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    return templates.TemplateResponse(request, "admin/users.html", {"app_name": settings.app_name})


@app.get("/admin/roles", response_class=HTMLResponse)
async def admin_roles_page(request: Request):
    return templates.TemplateResponse(request, "admin/roles.html", {"app_name": settings.app_name})


@app.get("/admin/menu-access", response_class=HTMLResponse)
async def admin_menu_access_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/menu_access.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/user-menu-rights", response_class=HTMLResponse)
async def admin_user_menu_rights_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/user_menu_rights.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/sessions", response_class=HTMLResponse)
async def admin_sessions_page(request: Request):
    return templates.TemplateResponse(request, "admin/sessions.html", {"app_name": settings.app_name})


@app.get("/admin/audit", response_class=HTMLResponse)
async def admin_audit_page(request: Request):
    return templates.TemplateResponse(request, "admin/audit.html", {"app_name": settings.app_name})


@app.get("/admin/login-alerts", response_class=HTMLResponse)
async def admin_login_alerts_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/login_notify.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/profile", response_class=HTMLResponse)
async def admin_profile_page(request: Request):
    return templates.TemplateResponse(request, "admin/profile.html", {"app_name": settings.app_name})


@app.get("/admin/change-password", response_class=HTMLResponse)
async def admin_change_password_page(request: Request):
    return templates.TemplateResponse(request, "admin/change-password.html", {"app_name": settings.app_name})


@app.get("/admin/voucher-entry", response_class=HTMLResponse)
async def admin_voucher_entry_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/voucher_entry.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/fin-item-classic", response_class=HTMLResponse)
async def admin_fin_item_classic_page(request: Request):
    return templates.TemplateResponse(request, "admin/fin_item_classic.html", {"app_name": settings.app_name})


@app.get("/admin/fin-pur", response_class=HTMLResponse)
async def admin_fin_pur_page(request: Request):
    return templates.TemplateResponse(request, "admin/fin_pur.html", {"app_name": settings.app_name})


@app.get("/admin/fin-inv-order", response_class=HTMLResponse)
async def admin_fin_inv_order_page(request: Request):
    return templates.TemplateResponse(request, "admin/fin_inv_order.html", {"app_name": settings.app_name})


@app.get("/admin/fin-inv-order/print", response_class=HTMLResponse)
@app.get("/admin/fin-inv-order/print/{inv_id}", response_class=HTMLResponse)
async def admin_fin_inv_order_print_page(request: Request, inv_id: int | None = None):
    """Standalone A4 Purchase Order print sheet (pixel match to VB6 / PO100)."""
    return templates.TemplateResponse(
        request,
        "admin/fin_inv_order_print.html",
        {"app_name": settings.app_name, "inv_id": inv_id},
    )


@app.get("/admin/purchase-automation", response_class=HTMLResponse)
async def admin_purchase_automation_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/purchase_automation.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/fin-items", response_class=HTMLResponse)
async def admin_fin_items_page(request: Request):
    return templates.TemplateResponse(request, "admin/fin_items.html", {"app_name": settings.app_name})


@app.get("/admin/gl-ledger-credit-summary", response_class=HTMLResponse)
async def admin_gl_ledger_credit_summary_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/gl_ledger_credit_summary.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/sales-dashboard", response_class=HTMLResponse)
async def admin_sales_dashboard_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/sales_dashboard.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/gl-ledger-mobile", response_class=HTMLResponse)
async def admin_gl_ledger_mobile_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/gl_ledger_mobile.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/gl-ledger-report", response_class=HTMLResponse)
async def admin_gl_ledger_report_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/gl_ledger_report.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/trial-balance-d2d-mobile", response_class=HTMLResponse)
async def admin_trial_balance_d2d_mobile_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/trial_balance_d2d_mobile.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/trial-balance-d2d", response_class=HTMLResponse)
async def admin_trial_balance_d2d_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/trial_balance_d2d.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/sms-email-scheduler", response_class=HTMLResponse)
async def admin_sms_email_scheduler_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/sms_email_scheduler.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/promotion-hub", response_class=HTMLResponse)
async def admin_promotion_hub_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/promotion_hub.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/cust-sms", response_class=HTMLResponse)
async def admin_cust_sms_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/cust_sms.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/delivery", response_class=HTMLResponse)
async def admin_delivery_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/delivery_dashboard.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/delivery-register", response_class=HTMLResponse)
async def admin_delivery_register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/delivery_register.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/customer-contacts", response_class=HTMLResponse)
async def admin_customer_contacts_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/customer_contacts.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/customer-import", response_class=HTMLResponse)
async def admin_customer_import_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/customer_import.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/customer-app-carts", response_class=HTMLResponse)
async def admin_customer_app_carts_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/customer_app_carts.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/whatsapp-bot", response_class=HTMLResponse)
async def admin_whatsapp_bot_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/whatsapp_bot.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/gemini-usage", response_class=HTMLResponse)
async def admin_gemini_usage_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/gemini_usage.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/voice-control", response_class=HTMLResponse)
async def admin_voice_control_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/voice_search_control.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/phone-osint", response_class=HTMLResponse)
async def admin_phone_osint_redirect(request: Request):
    return RedirectResponse(url="/admin/customer-contacts", status_code=302)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name, "env": settings.app_env}


def _wants_html(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    return "text/html" in accept and request.url.path.startswith(("/admin", "/login", "/dashboard", "/guest"))


@app.exception_handler(StarletteHTTPException)
async def html_http_error(request: Request, exc: StarletteHTTPException):
    if not _wants_html(request) or exc.status_code not in {403, 404, 500}:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    messages = {
        403: "You do not have access to this page.",
        404: "This page could not be found.",
        500: "The service is temporarily unavailable.",
    }
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "app_name": settings.app_name,
            "code": exc.status_code,
            "message": messages.get(exc.status_code, str(exc.detail)),
        },
        status_code=exc.status_code,
    )
