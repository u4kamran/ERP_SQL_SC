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
    is_guest_chat = request.url.path.startswith("/guest/chat")
    is_delivery_page = request.url.path == "/admin/delivery"
    is_delivery_registration = request.url.path.startswith(
        "/admin/delivery-register"
    )
    is_customer_import = request.url.path.startswith("/admin/customer-import")
    is_ocr_asset = request.url.path.startswith("/static/vendor/tesseract/")
    camera_policy = (
        "camera=(self)" if is_guest_scan or is_delivery_registration else "camera=()"
    )
    # Guest chat needs mic (voice search) and GPS pin sharing.
    microphone_policy = "microphone=(self)" if is_guest_chat else "microphone=()"
    geolocation_policy = (
        "geolocation=(self)"
        if is_delivery_page or is_guest_chat
        else "geolocation=()"
    )
    response.headers["Permissions-Policy"] = (
        f"{camera_policy}, {microphone_policy}, {geolocation_policy}"
    )
    worker_src = (
        "worker-src 'self' blob: https://cdn.jsdelivr.net; "
        if is_guest_scan or is_customer_import or is_ocr_asset
        else ""
    )
    # Guest chat: MediaRecorder blobs + Chrome speech network (desktop fallback).
    media_src = (
        "media-src 'self' blob: mediastream:; "
        if is_guest_scan or is_guest_chat
        else ""
    )
    if is_customer_import:
        connect_src = (
            "connect-src 'self' https://cdn.jsdelivr.net "
            "https://tessdata.projectnaptha.com; "
        )
    elif is_guest_chat:
        connect_src = (
            "connect-src 'self' https://www.google.com https://www.gstatic.com "
            "https://*.googleapis.com https://*.google.com; "
        )
    else:
        connect_src = "connect-src 'self'; "
    ocr_runtime_policy = (
        " 'wasm-unsafe-eval' 'unsafe-eval'"
        if is_customer_import or is_ocr_asset
        else ""
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        f"script-src 'self' 'unsafe-inline'{ocr_runtime_policy} https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data: blob:; "
        f"{connect_src}"
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
