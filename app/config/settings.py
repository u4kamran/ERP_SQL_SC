"""
Application configuration loaded from environment variables.

Uses pydantic-settings for validation and type coercion.
All secrets and environment-specific values must come from .env — never hardcoded.
"""

from functools import lru_cache
from typing import List

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"
_SHARED_SMTP_FILE = _PROJECT_ROOT.parent / "shared-smtp.env"

_env_files = [str(_ENV_FILE)]
if _SHARED_SMTP_FILE.exists():
    _env_files.append(str(_SHARED_SMTP_FILE))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(_env_files),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Shafique Departmental Store"
    company_name: str = "Shafique Departmental Store."
    app_env: str = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # URLs
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8000"

    # Database
    db_server: str = Field(..., alias="DB_SERVER")
    db_name: str = Field(..., alias="DB_NAME")
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_trust_server_certificate: str = "yes"
    db_encrypt: str = "no"

    business_db_server: str = ""
    business_db_name: str = "nsds2626"
    voucher_legacy_uid: int = Field(default=40, alias="VOUCHER_LEGACY_UID")

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_remember_me_expire_days: int = 30

    # Security
    bcrypt_rounds: int = 12
    csrf_secret_key: str = Field(..., min_length=32)
    csrf_cookie_name: str = "csrftoken"
    session_cookie_name: str = "session_id"
    secure_cookies: bool = False
    samesite_cookies: str = "lax"

    # Password policy
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    password_history_count: int = 5
    password_expiry_days: int = 90
    password_reset_token_expire_hours: int = 24

    # Account lockout
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 30

    # Session
    max_concurrent_sessions: int = 5

    # CORS
    cors_origins: str = "http://localhost:8000"

    # Host validation (comma-separated; use * to allow all)
    allowed_hosts: str = "*"

    # Cloudflare / Proxy
    trust_proxy_headers: bool = True
    cloudflare_ip_header: str = "CF-Connecting-IP"
    cloudflare_tunnel_hostname: str = "app.ahsteellab.com"

    # Email
    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_use_ssl: bool = False
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@ahsteellab.com"
    smtp_from_name: str = "Shafique Departmental Store"

    # WhatsApp Business Cloud API (automated PDF send + chatbot)
    whatsapp_enabled: bool = False
    whatsapp_api_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v21.0"
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_bot_enabled: bool = True

    # Guest web chat: require OTP proof of mobile ownership (WhatsApp delivery)
    guest_mobile_otp_required: bool = True
    guest_mobile_otp_dev_echo: bool = False

    # Gemini Vision + voice STT (guest chat / WhatsApp voice notes)
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.1-flash-lite"

    # Database sync (local SQL Server -> online SQL Server)
    sync_enabled: bool = False
    sync_remote_server: str = ""
    sync_remote_user: str = ""
    sync_remote_password: str = ""
    sync_remote_backup_share: str = ""
    sync_remote_restore_dir: str = ""
    sync_lan_only: bool = True
    sync_backup_dir: str = "data/sync/backups"
    sync_auth_db: bool = True
    sync_business_db: bool = True
    sync_interval_minutes: int = 1440
    sync_keep_local_backups: int = 2

    # Business day for sales reports (day starts 08:00, ends next day 05:00)
    business_day_start_hour: int = 8
    business_day_end_hour: int = 5

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Default admin seed
    default_admin_username: str = "admin"
    default_admin_email: str = "admin@ahsteellab.com"
    default_admin_password: str = "ChangeMe@2026!"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        hosts = [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]
        return hosts or ["*"]

    @property
    def database_url(self) -> str:
        """Build SQLAlchemy connection URL for auth database (pyodbc)."""
        return self._build_mssql_url(self.db_name)

    @property
    def business_database_url(self) -> str:
        """Build SQLAlchemy connection URL for legacy business database."""
        server = self.business_db_server or self.db_server
        return self._build_mssql_url(self.business_db_name, server=server)

    def _build_mssql_url(self, database: str, server: str | None = None) -> str:
        from urllib.parse import quote_plus

        odbc_connect = (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER={server or self.db_server};"
            f"DATABASE={database};"
            f"UID={self.db_user};"
            f"PWD={self.db_password};"
            f"TrustServerCertificate={self.db_trust_server_certificate};"
            f"Encrypt={self.db_encrypt};"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_connect)}"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.secure_cookies or self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
