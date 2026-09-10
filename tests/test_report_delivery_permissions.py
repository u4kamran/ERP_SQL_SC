"""Unit tests for per-report delivery permissions."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from app.api.deps import CurrentUser, require_report_delivery
from app.services.menu_access_service import _action_codes_for_view, menu_permission_codes


def _user(*perms: str) -> CurrentUser:
    return CurrentUser(
        user_id=1,
        username="tester",
        roles=["USER"],
        permissions=list(perms),
        session_id="s1",
    )


def _call(dep, user: CurrentUser) -> CurrentUser:
    return asyncio.run(dep(current_user=user))


def test_each_report_has_own_delivery_actions():
    gl = {c for _a, _l, c in _action_codes_for_view("reports.gl_ledger.view")}
    detailed = {c for _a, _l, c in _action_codes_for_view("reports.gl_ledger_detailed.view")}
    stock = {c for _a, _l, c in _action_codes_for_view("reports.stock_balance_d2d.view")}
    credit = {c for _a, _l, c in _action_codes_for_view("reports.gl_credit_summary.view")}
    assert "reports.gl_ledger.email" in gl
    assert "reports.gl_ledger.whatsapp" in gl
    assert "reports.gl_ledger_detailed.email" in detailed
    assert "reports.gl_ledger_detailed.whatsapp" in detailed
    assert "reports.stock_balance_d2d.email" in stock
    assert "reports.stock_balance_d2d.whatsapp" not in stock
    assert "reports.gl_credit_summary.email" in credit
    assert "reports.gl_ledger.email" not in stock
    assert "reports.gl_ledger_detailed.email" not in stock


def test_menu_permission_codes_lists_per_report():
    codes = menu_permission_codes()
    assert "reports.stock_balance_d2d.view" in codes
    assert "reports.stock_balance_d2d.email" in codes
    assert "reports.gl_credit_summary.view" in codes
    assert "reports.trial_balance_d2d.whatsapp" in codes
    assert "reports.gl_ledger_mobile.view" in codes
    assert "reports.gl_ledger_detailed.view" in codes
    assert "reports.gl_ledger_detailed.email" in codes
    assert "reports.gl_ledger_detailed.whatsapp" in codes


def test_stock_email_requires_stock_email_perm():
    dep = require_report_delivery(
        "reports.stock_balance_d2d.view",
        action_permissions=("reports.stock_balance_d2d.email",),
        denied_detail="You do not have permission to email this report.",
    )
    # Has GL email but not stock email → denied
    user = _user("reports.stock_balance_d2d.view", "reports.gl_ledger.email")
    with pytest.raises(HTTPException) as exc:
        _call(dep, user)
    assert exc.value.status_code == 403

    ok = _user("reports.stock_balance_d2d.view", "reports.stock_balance_d2d.email")
    assert _call(dep, ok).username == "tester"


def test_stock_view_alone_cannot_use_gl_view():
    """Stock page view is independent of GL Ledger view."""
    dep = require_report_delivery(
        "reports.stock_balance_d2d.view",
        action_permissions=("reports.stock_balance_d2d.email",),
        denied_detail="denied",
    )
    user = _user("reports.gl_ledger.view", "reports.stock_balance_d2d.email")
    with pytest.raises(HTTPException) as exc:
        _call(dep, user)
    assert exc.value.detail == "Insufficient permissions."


def test_admin_full_bypasses():
    dep = require_report_delivery(
        "reports.stock_balance_d2d.view",
        action_permissions=("reports.stock_balance_d2d.email",),
        denied_detail="denied",
    )
    assert _call(dep, _user("auth.admin.full")).has_permission("reports.stock_balance_d2d.email")


def test_menu_access_keeps_separate_rows_for_separate_perms():
    from unittest.mock import MagicMock

    from app.services import menu_access_service as mas

    links = [
        {"label": "GL Ledger Report", "path": "/a", "permission": "reports.gl_ledger.view", "icon": "", "description": ""},
        {"label": "Stock Balance D2D", "path": "/b", "permission": "reports.stock_balance_d2d.view", "icon": "", "description": ""},
    ]
    groups = [{"title": "Reports", "links": links}]

    gl = MagicMock(PermissionId=1, PermissionCode="reports.gl_ledger.view")
    st = MagicMock(PermissionId=2, PermissionCode="reports.stock_balance_d2d.view")

    original = mas.get_internal_link_groups
    original_map = mas._permission_map
    original_granted = mas._active_role_permission_ids
    try:
        mas.get_internal_link_groups = lambda: groups
        mas._permission_map = lambda _db: {
            "reports.gl_ledger.view": gl,
            "reports.stock_balance_d2d.view": st,
        }
        mas._active_role_permission_ids = lambda _db, _rid: {1}

        role = MagicMock(RoleId=1, RoleCode="ADMIN", RoleName="Admin", IsSystemRole=True)
        catalog = mas.build_menu_access_catalog(MagicMock(), role)
        assert len(catalog.groups[0].items) == 2
        labels = {i.label for i in catalog.groups[0].items}
        assert "GL Ledger Report" in labels
        assert "Stock Balance D2D" in labels
        by_label = {i.label: i for i in catalog.groups[0].items}
        assert by_label["GL Ledger Report"].granted is True
        assert by_label["Stock Balance D2D"].granted is False
    finally:
        mas.get_internal_link_groups = original
        mas._permission_map = original_map
        mas._active_role_permission_ids = original_granted
