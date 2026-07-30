"""Business database (nsds2626) engine and session — read/write legacy tables."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings

business_engine = create_engine(
    settings.business_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.debug,
)

BusinessSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=business_engine)


def get_business_db() -> Generator[Session, None, None]:
    """FastAPI dependency for legacy business database session."""
    db = BusinessSessionLocal()
    try:
        yield db
    finally:
        db.close()
