"""Application entry point for uvicorn."""

import uvicorn

from app.config.settings import settings
from app.utils.single_instance import ensure_single_instance

if __name__ == "__main__":
    ensure_single_instance(settings.host, settings.port)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        proxy_headers=settings.trust_proxy_headers,
        forwarded_allow_ips="*" if settings.trust_proxy_headers else "127.0.0.1",
        timeout_keep_alive=75,
        timeout_graceful_shutdown=10,
        limit_concurrency=40,
    )
