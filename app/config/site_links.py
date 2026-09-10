"""Central site link registry for dashboard and navigation."""

from __future__ import annotations

from typing import TypedDict


class SiteLink(TypedDict, total=False):
    label: str
    path: str
    icon: str
    description: str
    permission: str


class LinkGroup(TypedDict):
    title: str
    links: list[SiteLink]


INTERNAL_LINK_GROUPS: list[LinkGroup] = [
    {
        "title": "Main",
        "links": [
            {
                "label": "Dashboard",
                "path": "/dashboard",
                "icon": "bi-speedometer2",
                "description": "Home overview and quick actions",
            },
            {
                "label": "My Profile",
                "path": "/admin/profile",
                "icon": "bi-person",
                "description": "Account details and preferences",
            },
            {
                "label": "Change Password",
                "path": "/admin/change-password",
                "icon": "bi-key",
                "description": "Update your login password",
            },
        ],
    },
    {
        "title": "Accounting",
        "links": [
            {
                "label": "Voucher Entry",
                "path": "/admin/voucher-entry",
                "icon": "bi-journal-plus",
                "description": "Easy voucher entry — same GL tables as VB6",
                "permission": "gl.voucher.view",
            },
        ],
    },
    {
        "title": "Inventory & Sales",
        "links": [
            {
                "label": "Sales Dashboard",
                "path": "/admin/sales-dashboard",
                "icon": "bi-graph-up-arrow",
                "description": "KPIs, trends, and top invoices",
                "permission": "reports.sales_dashboard.view",
            },
            {
                "label": "Item Info",
                "path": "/admin/fin-item-classic",
                "icon": "bi-window-desktop",
                "description": "Classic item entry and lookup (VB6 Item Info)",
                "permission": "inventory.fin_item.view",
            },
            {
                "label": "Purchase Receipt (VB6)",
                "path": "/admin/fin-pur",
                "icon": "bi-receipt",
                "description": "GRN / Purchase Receipt — Fin_PurM parity",
                "permission": "inventory.fin_pur.view",
            },
            {
                "label": "Purchase Order (VB6)",
                "path": "/admin/fin-inv-order",
                "icon": "bi-cart-check",
                "description": "Supplier PO — Fin_InvM_Order parity",
                "permission": "inventory.fin_inv_order.view",
            },
            {
                "label": "Purchase Automation",
                "path": "/admin/purchase-automation",
                "icon": "bi-robot",
                "description": "Upload supplier invoice → AI extract → review → Save",
                "permission": "inventory.fin_pur.create",
            },
            {
                "label": "Items (FIN_ITEM)",
                "path": "/admin/fin-items",
                "icon": "bi-box-seam",
                "description": "Modern item list and API view",
                "permission": "inventory.fin_item.view",
            },
            {
                "label": "Item Image Manager",
                "path": "/admin/item-images",
                "icon": "bi-images",
                "description": "Search, review, and link product images (separate tables)",
                "permission": "inventory.item_images.view",
            },
        ],
    },
    {
        "title": "Delivery",
        "links": [
            {
                "label": "Delivery Command Center",
                "path": "/admin/delivery",
                "icon": "bi-truck",
                "description": "Synchronize invoices, assign riders, and update deliveries",
                "permission": "delivery.orders.view",
            },
            {
                "label": "Register Delivery",
                "path": "/admin/delivery-register",
                "icon": "bi-qr-code-scan",
                "description": "Scan GP_TIME and register an invoice for delivery",
                "permission": "delivery.orders.update",
            },
        ],
    },
    {
        "title": "Reports",
        "links": [
            {
                "label": "GL Ledger (Mobile)",
                "path": "/admin/gl-ledger-mobile",
                "icon": "bi-phone",
                "description": "Generate and view ledger PDF on mobile",
                "permission": "reports.gl_ledger_mobile.view",
            },
            {
                "label": "GL Ledger Report",
                "path": "/admin/gl-ledger-report",
                "icon": "bi-journal-text",
                "description": "Desktop GL ledger PDF and email",
                "permission": "reports.gl_ledger.view",
            },
            {
                "label": "Customer Ledger (Detailed)",
                "path": "/admin/gl-ledger-detailed",
                "icon": "bi-journal-richtext",
                "description": "GL ledger plus invoice line detail (Gate Pass, Qty, Rate, GST)",
                "permission": "reports.gl_ledger_detailed.view",
            },
            {
                "label": "Credit Summary Ledger",
                "path": "/admin/gl-ledger-credit-summary",
                "icon": "bi-journal-check",
                "description": "Credit summary ledger report",
                "permission": "reports.gl_credit_summary.view",
            },
            {
                "label": "Trial Balance D2D",
                "path": "/admin/trial-balance-d2d",
                "icon": "bi-table",
                "description": "Trial Balance Date to Date report",
                "permission": "reports.trial_balance_d2d.view",
            },
            {
                "label": "Trial Balance D2D (Mobile)",
                "path": "/admin/trial-balance-d2d-mobile",
                "icon": "bi-phone",
                "description": "Generate and share trial balance PDF on mobile",
                "permission": "reports.trial_balance_d2d_mobile.view",
            },
            {
                "label": "Stock Balance D2D",
                "path": "/admin/stock-balance-d2d",
                "icon": "bi-boxes",
                "description": "Stock Balance Date to Date report",
                "permission": "reports.stock_balance_d2d.view",
            },
            {
                "label": "SMS Sales Email",
                "path": "/admin/sms-email-scheduler",
                "icon": "bi-envelope-paper",
                "description": "Scheduled sales email automation",
                "permission": "reports.sms_email.manage",
            },
            {
                "label": "CUST_SMS Master",
                "path": "/admin/cust-sms",
                "icon": "bi-phone-vibrate",
                "description": "Create, edit, delete Customer SMS (CUST_SMS) records",
                "permission": "marketing.cust_sms.view",
            },
            {
                "label": "Import Customer File",
                "path": "/admin/customer-import",
                "icon": "bi-file-earmark-text",
                "description": "OCR, translate, review, and import customers",
                "permission": "marketing.cust_sms.create",
            },
            {
                "label": "Customer Contacts",
                "path": "/admin/customer-contacts",
                "icon": "bi-people-fill",
                "description": "Customer emails, phones, and social media for marketing",
                "permission": "marketing.customer_contacts.view",
            },
            {
                "label": "Promotion Hub",
                "path": "/admin/promotion-hub",
                "icon": "bi-megaphone-fill",
                "description": "Send promotions via WhatsApp, email, and social platforms",
                "permission": "marketing.promotion.view",
            },
            {
                "label": "Customer App Carts",
                "path": "/admin/customer-app-carts",
                "icon": "bi-cart-check",
                "description": "Saved carts from the Shafique customer mobile app (not WhatsApp WO)",
                "permission": "marketing.customer_app_carts.view",
            },
            {
                "label": "WhatsApp Chatbot",
                "path": "/admin/whatsapp-bot",
                "icon": "bi-whatsapp",
                "description": "Offline web chat and WhatsApp Cloud API chatbot inbox",
                "permission": "marketing.whatsapp_bot.view",
            },
            {
                "label": "Gemini Usage",
                "path": "/admin/gemini-usage",
                "icon": "bi-cpu",
                "description": "Gemini tokens, estimated cost, and remaining prepaid budget",
                "permission": "marketing.gemini_usage.view",
            },
            {
                "label": "Voice Search Control",
                "path": "/admin/voice-control",
                "icon": "bi-mic-mute",
                "description": "Voice limits, budget, and misuse audit by mobile and search text",
                "permission": "marketing.voice_control.view",
            },
            {
                "label": "Item Search",
                "path": "/admin/item-search",
                "icon": "bi-search",
                "description": "Product autocomplete settings, aliases, and empty-search report",
                "permission": "marketing.item_search.view",
            },
        ],
    },
    {
        "title": "Administration",
        "links": [
            {
                "label": "Users",
                "path": "/admin/users",
                "icon": "bi-people",
                "description": "Manage user accounts",
                "permission": "auth.users.view",
            },
            {
                "label": "Roles",
                "path": "/admin/roles",
                "icon": "bi-shield-check",
                "description": "Create roles and assign permissions",
                "permission": "auth.roles.view",
            },
            {
                "label": "Menu Rights",
                "path": "/admin/menu-access",
                "icon": "bi-toggles2",
                "description": "Per menu View / Add / Edit / Delete for each role",
                "permission": "auth.roles.view",
            },
            {
                "label": "User Menu Rights",
                "path": "/admin/user-menu-rights",
                "icon": "bi-person-check",
                "description": "Show or hide menus for a single user",
                "permission": "auth.roles.manage",
            },
            {
                "label": "Sessions",
                "path": "/admin/sessions",
                "icon": "bi-display",
                "description": "Active login sessions",
                "permission": "auth.sessions.view",
            },
            {
                "label": "Audit Logs",
                "path": "/admin/audit",
                "icon": "bi-journal-text",
                "description": "Security and activity audit trail",
                "permission": "auth.audit.view",
            },
            {
                "label": "Login Alerts",
                "path": "/admin/login-alerts",
                "icon": "bi-envelope-exclamation",
                "description": "Email a default address whenever any user signs in",
                "permission": "auth.login_notify.view",
            },
            {
                "label": "OTP / SMS Control",
                "path": "/admin/otp-sms-control",
                "icon": "bi-shield-lock",
                "description": "Master enable / disable OTP SMS for web and mobile",
                "permission": "auth.otp_sms_control.view",
            },
        ],
    },
]

EXTERNAL_LINKS: list[SiteLink] = [
    {
        "label": "Public ERP Login",
        "path": "/login",
        "icon": "bi-box-arrow-in-right",
        "description": "Share with staff for remote access",
    },
    {
        "label": "Guest Price Scan",
        "path": "/guest/scan",
        "icon": "bi-upc-scan",
        "description": "Public barcode price lookup for customers",
    },
    {
        "label": "API Documentation",
        "path": "/api/docs",
        "icon": "bi-code-square",
        "description": "Swagger API reference",
    },
    {
        "label": "Health Check",
        "path": "/health",
        "icon": "bi-heart-pulse",
        "description": "System health status endpoint",
    },
    {
        "label": "AH Steel Lab",
        "path": "https://ahsteellab.com",
        "icon": "bi-globe2",
        "description": "Company website",
    },
]


def _full_url(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{base_url.rstrip('/')}{path}"


def get_internal_link_groups() -> list[LinkGroup]:
    return INTERNAL_LINK_GROUPS


def get_external_links(base_url: str) -> list[dict]:
    return [
        {
            **link,
            "url": _full_url(base_url, link["path"]),
            "external": not link["path"].startswith("/"),
        }
        for link in EXTERNAL_LINKS
    ]


def get_flat_internal_links(base_url: str) -> list[dict]:
    links: list[dict] = []
    for group in INTERNAL_LINK_GROUPS:
        for link in group["links"]:
            links.append(
                {
                    **link,
                    "group": group["title"],
                    "url": _full_url(base_url, link["path"]),
                    "external": False,
                }
            )
    return links
