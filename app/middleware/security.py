"""Application middleware."""

from starlette.requests import Request
from starlette.responses import Response

from app.security.csrf import generate_csrf_token


async def security_headers_middleware(request: Request, call_next) -> Response:
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    is_guest_scan = request.url.path.startswith("/guest")
    camera_policy = "camera=(self)" if is_guest_scan else "camera=()"
    response.headers["Permissions-Policy"] = f"{camera_policy}, microphone=(), geolocation=()"
    worker_src = "worker-src 'self' blob:; " if is_guest_scan else ""
    media_src = "media-src 'self' blob:; " if is_guest_scan else ""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-src 'self' blob:; "
        "object-src 'self' blob:; "
        f"{worker_src}"
        f"{media_src}"
    )
    return response


async def csrf_middleware(request: Request, call_next) -> Response:
    """Set CSRF cookie on GET requests for form protection."""
    response = await call_next(request)
    if request.method == "GET" and "csrftoken" not in request.cookies:
        from app.config.settings import settings

        token = generate_csrf_token()
        response.set_cookie(
            key=settings.csrf_cookie_name,
            value=token,
            httponly=False,
            secure=settings.cookie_secure,
            samesite=settings.samesite_cookies,
        )
    return response
