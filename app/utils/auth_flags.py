"""Authorization helpers shared by API and services."""

from __future__ import annotations


def is_super_admin(roles: list[str], permissions: list[str]) -> bool:
    """Site links and other super-only UI — SUPER_ADMIN or auth.admin.full only."""
    if "auth.admin.full" in permissions:
        return True
    return "SUPER_ADMIN" in roles
