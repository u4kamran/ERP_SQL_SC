"""Block admin HTML pages the user is not granted in User Menu Rights."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

from app.config.settings import settings
from app.database.session import SessionLocal
from app.security.jwt import decode_token
from app.services.user_menu_rights_service import get_session_menu_info, path_is_allowed
from app.utils.auth_flags import is_super_admin


ALWAYS_OPEN_PREFIXES = (
    "/static/",
    "/api/",
    "/login",
    "/health",
    "/guest/",
    "/docs",
    "/redoc",
    "/openapi",
)

ALWAYS_OPEN_PATHS = {
    "/",
    "/dashboard",
    "/admin/profile",
    "/admin/change-password",
    "/admin/user-menu-rights",
}


def _forbidden_html(app_name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Access Denied - {app_name}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5" style="max-width:34rem">
  <div class="card shadow-sm border-0">
    <div class="card-body p-4 text-center">
      <h1 class="h4 mb-3">Access Denied</h1>
      <p class="text-muted mb-4">You do not have permission to access this module.</p>
      <a class="btn btn-primary" href="/dashboard">Back to Dashboard</a>
    </div>
  </div>
</div>
</body></html>"""


async def menu_access_guard_middleware(request: Request, call_next) -> Response:
    path = request.url.path
    if request.method != "GET":
        return await call_next(request)
    if any(path.startswith(prefix) for prefix in ALWAYS_OPEN_PREFIXES):
        return await call_next(request)
    if path in ALWAYS_OPEN_PATHS or not (
        path.startswith("/admin/") or path == "/dashboard"
    ):
        return await call_next(request)

    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
    if not token:
        return await call_next(request)

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub") or 0)
    except Exception:  # noqa: BLE001
        return await call_next(request)
    if not user_id:
        return await call_next(request)

    db = SessionLocal()
    try:
        roles = list(payload.get("roles") or [])
        permissions = list(payload.get("permissions") or [])
        if is_super_admin(roles, permissions):
            return await call_next(request)
        info = get_session_menu_info(db, user_id)
        if path_is_allowed(info, path):
            return await call_next(request)
        return HTMLResponse(
            content=_forbidden_html(settings.app_name),
            status_code=403,
        )
    finally:
        db.close()
