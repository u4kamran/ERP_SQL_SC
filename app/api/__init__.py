"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, users, roles, permissions, sessions, audit, profile, fin_item, fin_item_classic, gl_ledger_report, gl_ledger_credit_summary, trial_balance_d2d, sms_email_scheduler, sales_dashboard, sales_dashboard_email, guest_price_lookup, voucher_entry, customer_contacts, customer_import, promotion_hub, cust_sms, delivery, whatsapp_bot, fin_pur, fin_inv_order, purchase_automation, user_menu_rights

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(
    user_menu_rights.router,
    prefix="/user-menu-rights",
    tags=["User Menu Rights"],
)
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(fin_item.router, prefix="/fin-items", tags=["FIN_ITEM"])
api_router.include_router(fin_item_classic.router, prefix="/fin-item-classic", tags=["FIN_ITEM Classic"])
api_router.include_router(gl_ledger_report.router, prefix="/reports/gl-ledger", tags=["GL Ledger Report"])
api_router.include_router(gl_ledger_credit_summary.router, prefix="/reports/gl-ledger-credit", tags=["GL Credit Summary Ledger"])
api_router.include_router(trial_balance_d2d.router, prefix="/reports/trial-balance-d2d", tags=["Trial Balance D2D"])
api_router.include_router(sms_email_scheduler.router, prefix="/reports/sms-email", tags=["SMS Email Scheduler"])
api_router.include_router(sales_dashboard.router, prefix="/reports/sales-dashboard", tags=["Sales Dashboard"])
api_router.include_router(sales_dashboard_email.router, prefix="/reports/sales-dashboard/email", tags=["Sales Dashboard Email"])
api_router.include_router(guest_price_lookup.router, prefix="/public/price-lookup", tags=["Guest Price Lookup"])
api_router.include_router(voucher_entry.router, prefix="/vouchers", tags=["Voucher Entry"])
api_router.include_router(fin_pur.router, prefix="/fin-pur", tags=["Purchase Receipt"])
api_router.include_router(fin_inv_order.router, prefix="/fin-inv-order", tags=["Purchase Order"])
api_router.include_router(
    purchase_automation.router,
    prefix="/purchase-automation",
    tags=["Purchase Automation"],
)
api_router.include_router(customer_contacts.router, prefix="/marketing/customer-contacts", tags=["Customer Contacts"])
api_router.include_router(customer_import.router, prefix="/marketing/customer-import", tags=["Customer Import"])
api_router.include_router(promotion_hub.router, prefix="/marketing/promotion", tags=["Promotion Hub"])
api_router.include_router(cust_sms.router, prefix="/cust-sms", tags=["CUST_SMS"])
api_router.include_router(delivery.router, prefix="/delivery", tags=["Delivery"])
api_router.include_router(
    whatsapp_bot.router,
    prefix="/marketing/whatsapp-bot",
    tags=["WhatsApp Chatbot"],
)
api_router.include_router(
    whatsapp_bot.public_router,
    prefix="/public/whatsapp",
    tags=["WhatsApp Public"],
)
