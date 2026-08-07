"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import api_router
from app.config.settings import settings
from app.config.site_links import get_external_links, get_internal_link_groups
from app.logging.logger import logger
from app.middleware.security import csrf_middleware, security_headers_middleware
from app.scheduler.delivery_invoice_scheduler import get_delivery_invoice_scheduler
from app.scheduler.sms_email_scheduler import get_scheduler_runner
from app.scheduler.sales_dashboard_email_scheduler import get_sales_dashboard_email_runner

from app.services.email_service import EmailService

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
templates.env.globals["base_url"] = settings.base_url.rstrip("/")
templates.env.globals["internal_link_groups"] = get_internal_link_groups()
templates.env.globals["external_links"] = get_external_links(settings.base_url)
templates.env.globals["smtp_configured"] = lambda: EmailService().is_configured()
templates.env.globals["smtp_hint"] = lambda: EmailService().configuration_hint()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s [%s]", settings.app_name, settings.app_env)
    runner = get_scheduler_runner()
    sales_email_runner = get_sales_dashboard_email_runner()
    delivery_invoice_runner = get_delivery_invoice_scheduler()
    await runner.start()
    await sales_email_runner.start()
    await delivery_invoice_runner.start()
    yield
    await delivery_invoice_runner.stop()
    await sales_email_runner.stop()
    await runner.stop()
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
    return templates.TemplateResponse(
        request,
        "guest/chat.html",
        {
            "app_name": settings.app_name,
            "guest_mobile_otp_required": bool(settings.guest_mobile_otp_required),
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


@app.get("/admin/sessions", response_class=HTMLResponse)
async def admin_sessions_page(request: Request):
    return templates.TemplateResponse(request, "admin/sessions.html", {"app_name": settings.app_name})


@app.get("/admin/audit", response_class=HTMLResponse)
async def admin_audit_page(request: Request):
    return templates.TemplateResponse(request, "admin/audit.html", {"app_name": settings.app_name})


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


@app.get("/admin/whatsapp-bot", response_class=HTMLResponse)
async def admin_whatsapp_bot_page(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/whatsapp_bot.html",
        {"app_name": settings.app_name},
    )


@app.get("/admin/phone-osint", response_class=HTMLResponse)
async def admin_phone_osint_redirect(request: Request):
    return RedirectResponse(url="/admin/customer-contacts", status_code=302)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name, "env": settings.app_env}
