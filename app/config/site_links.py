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
        "title": "Inventory & Sales",
        "links": [
            {
                "label": "Sales Dashboard",
                "path": "/admin/sales-dashboard",
                "icon": "bi-graph-up-arrow",
                "description": "KPIs, trends, and top invoices",
                "permission": "inventory.fin_item.view",
            },
            {
                "label": "Item Master (VB6)",
                "path": "/admin/fin-item-classic",
                "icon": "bi-window-desktop",
                "description": "Classic item entry and lookup",
                "permission": "inventory.fin_item.view",
            },
            {
                "label": "Items (FIN_ITEM)",
                "path": "/admin/fin-items",
                "icon": "bi-box-seam",
                "description": "Modern item list and API view",
                "permission": "inventory.fin_item.view",
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
                "permission": "inventory.fin_item.view",
            },
            {
                "label": "GL Ledger Report",
                "path": "/admin/gl-ledger-report",
                "icon": "bi-journal-text",
                "description": "Desktop GL ledger PDF and email",
                "permission": "inventory.fin_item.view",
            },
            {
                "label": "Credit Summary Ledger",
                "path": "/admin/gl-ledger-credit-summary",
                "icon": "bi-journal-check",
                "description": "Credit summary ledger report",
                "permission": "inventory.fin_item.view",
            },
            {
                "label": "SMS Sales Email",
                "path": "/admin/sms-email-scheduler",
                "icon": "bi-envelope-paper",
                "description": "Scheduled sales email automation",
                "permission": "inventory.fin_item.view",
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
                "description": "Roles and permissions",
                "permission": "auth.roles.view",
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
