"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, users, roles, permissions, sessions, audit, profile, fin_item, fin_item_classic, gl_ledger_report, gl_ledger_credit_summary, sms_email_scheduler, sales_dashboard, guest_price_lookup

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(fin_item.router, prefix="/fin-items", tags=["FIN_ITEM"])
api_router.include_router(fin_item_classic.router, prefix="/fin-item-classic", tags=["FIN_ITEM Classic"])
api_router.include_router(gl_ledger_report.router, prefix="/reports/gl-ledger", tags=["GL Ledger Report"])
api_router.include_router(gl_ledger_credit_summary.router, prefix="/reports/gl-ledger-credit", tags=["GL Credit Summary Ledger"])
api_router.include_router(sms_email_scheduler.router, prefix="/reports/sms-email", tags=["SMS Email Scheduler"])
api_router.include_router(sales_dashboard.router, prefix="/reports/sales-dashboard", tags=["Sales Dashboard"])
api_router.include_router(guest_price_lookup.router, prefix="/public/price-lookup", tags=["Guest Price Lookup"])
