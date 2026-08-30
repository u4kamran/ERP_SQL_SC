"""Reset one Pakistan mobile so it can request OTP and register again.

Clears guest-web OTP (data/mobile_otp.json), customer-app OTP, SMS_DB_ OTP
queue rows, customer-app carts for that mobile, and the CUST_SMS row that
makes lookup return "already registered".

Usage (from ERP repo root):

  venv\\Scripts\\python.exe scripts\\reset_otp_for_mobile.py 03009438280
  venv\\Scripts\\python.exe scripts\\reset_otp_for_mobile.py 03009438280 --dry-run

Accepts 03XXXXXXXXX, 3XXXXXXXXX, 92XXXXXXXXXX, or +92….
Does not print OTP codes or secrets. Does not restart ERP.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from app.database.business_session import BusinessSessionLocal  # noqa: E402

GUEST_OTP_FILE = ROOT / "data" / "mobile_otp.json"
ERP_BASE = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"

# Same digit-strip as CUST_SMS lookup in customer_app_cart_repository.
_SQL_RIGHT10 = """
RIGHT(
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        LTRIM(RTRIM(ISNULL({col}, ''))),
        ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''),
    10
)
"""


def digits_only(raw: str) -> str:
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def parse_mobile(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        raise SystemExit("Usage: scripts/reset_otp_for_mobile.py 03XXXXXXXXX [--dry-run]")
    digits = digits_only(value)
    if len(digits) < 10:
        raise SystemExit("Invalid mobile: need at least 10 digits (Pakistan 03XXXXXXXXX).")
    key = digits[-10:]
    if not key.startswith("3"):
        raise SystemExit(f"Invalid Pakistan mobile key {key!r}: last 10 digits must start with 3.")
    return key


def variants(key: str) -> dict[str, str]:
    return {
        "key": key,
        "local": f"0{key}",
        "e164": f"92{key}",
    }


def key_matches(value: str, key: str) -> bool:
    digits = digits_only(str(value or ""))
    return len(digits) >= 10 and digits[-10:] == key


def table_exists(db, table_name: str) -> bool:
    allowed = {
        "customer_app_otp",
        "SMS_DB_",
        "CUST_SMS",
        "customer_app_carts",
        "customer_app_cart_lines",
        "customer_app_cart_status_history",
    }
    if table_name not in allowed:
        return False
    row = db.execute(
        text(f"SELECT OBJECT_ID(N'dbo.{table_name}', N'U')"),
    ).scalar()
    return row is not None


def rowcount(result) -> int:
    n = result.rowcount
    return int(n) if n is not None and n >= 0 else 0


def clear_guest_json(key: str, *, dry_run: bool) -> tuple[int, int]:
    pending_removed = 0
    verified_removed = 0
    if not GUEST_OTP_FILE.exists():
        return 0, 0
    try:
        data = json.loads(GUEST_OTP_FILE.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    pending = data.get("pending") if isinstance(data.get("pending"), dict) else {}
    verified = data.get("verified") if isinstance(data.get("verified"), dict) else {}

    def drop(store: dict) -> int:
        removed = 0
        for store_key, row in list(store.items()):
            phone = ""
            if isinstance(row, dict):
                phone = str(row.get("phone") or "")
            if key_matches(store_key, key) or key_matches(phone, key):
                store.pop(store_key, None)
                removed += 1
        return removed

    pending_removed = drop(pending)
    verified_removed = drop(verified)
    if not dry_run and (pending_removed or verified_removed):
        data["pending"] = pending
        data["verified"] = verified
        GUEST_OTP_FILE.write_text(
            json.dumps(data, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
    return pending_removed, verified_removed


def clear_sql(key: str, *, dry_run: bool) -> dict[str, int]:
    counts = {
        "customer_app_otp": 0,
        "SMS_DB_": 0,
        "customer_app_cart_lines": 0,
        "customer_app_cart_status_history": 0,
        "customer_app_carts": 0,
        "CUST_SMS": 0,
    }
    local = f"0{key}"
    e164 = f"92{key}"
    db = BusinessSessionLocal()
    try:
        if table_exists(db, "customer_app_otp"):
            if dry_run:
                counts["customer_app_otp"] = int(
                    db.execute(
                        text(
                            """
                            SELECT COUNT(1)
                            FROM dbo.customer_app_otp
                            WHERE mobile_key = :key
                               OR RIGHT(REPLACE(ISNULL(mobile_display, ''), '+', ''), 10) = :key
                            """
                        ),
                        {"key": key},
                    ).scalar()
                    or 0
                )
            else:
                counts["customer_app_otp"] = rowcount(
                    db.execute(
                        text(
                            """
                            DELETE FROM dbo.customer_app_otp
                            WHERE mobile_key = :key
                               OR RIGHT(REPLACE(ISNULL(mobile_display, ''), '+', ''), 10) = :key
                            """
                        ),
                        {"key": key},
                    )
                )

        if table_exists(db, "SMS_DB_"):
            sms_where = """
                (
                    RIGHT(REPLACE(REPLACE(ISNULL(RECIPIENT, ''), '+', ''), ' ', ''), 10) = :key
                    OR REPLACE(ISNULL(RECIPIENT, ''), '+', '') IN (:local, :e164, :key)
                )
                AND (
                    BODY LIKE 'Your verification code is %'
                    OR BODY LIKE '%verification code%'
                )
            """
            if dry_run:
                counts["SMS_DB_"] = int(
                    db.execute(
                        text(f"SELECT COUNT(1) FROM dbo.SMS_DB_ WHERE {sms_where}"),
                        {"key": key, "local": local, "e164": e164},
                    ).scalar()
                    or 0
                )
            else:
                counts["SMS_DB_"] = rowcount(
                    db.execute(
                        text(f"DELETE FROM dbo.SMS_DB_ WHERE {sms_where}"),
                        {"key": key, "local": local, "e164": e164},
                    )
                )

        cart_filter = "mobile_key = :key"
        if table_exists(db, "customer_app_carts"):
            if table_exists(db, "customer_app_cart_lines"):
                if dry_run:
                    counts["customer_app_cart_lines"] = int(
                        db.execute(
                            text(
                                f"""
                                SELECT COUNT(1)
                                FROM dbo.customer_app_cart_lines
                                WHERE cart_id IN (
                                    SELECT id FROM dbo.customer_app_carts WHERE {cart_filter}
                                )
                                """
                            ),
                            {"key": key},
                        ).scalar()
                        or 0
                    )
                else:
                    counts["customer_app_cart_lines"] = rowcount(
                        db.execute(
                            text(
                                f"""
                                DELETE FROM dbo.customer_app_cart_lines
                                WHERE cart_id IN (
                                    SELECT id FROM dbo.customer_app_carts WHERE {cart_filter}
                                )
                                """
                            ),
                            {"key": key},
                        )
                    )
            if table_exists(db, "customer_app_cart_status_history"):
                if dry_run:
                    counts["customer_app_cart_status_history"] = int(
                        db.execute(
                            text(
                                f"""
                                SELECT COUNT(1)
                                FROM dbo.customer_app_cart_status_history
                                WHERE cart_id IN (
                                    SELECT id FROM dbo.customer_app_carts WHERE {cart_filter}
                                )
                                """
                            ),
                            {"key": key},
                        ).scalar()
                        or 0
                    )
                else:
                    counts["customer_app_cart_status_history"] = rowcount(
                        db.execute(
                            text(
                                f"""
                                DELETE FROM dbo.customer_app_cart_status_history
                                WHERE cart_id IN (
                                    SELECT id FROM dbo.customer_app_carts WHERE {cart_filter}
                                )
                                """
                            ),
                            {"key": key},
                        )
                    )
            if dry_run:
                counts["customer_app_carts"] = int(
                    db.execute(
                        text(f"SELECT COUNT(1) FROM dbo.customer_app_carts WHERE {cart_filter}"),
                        {"key": key},
                    ).scalar()
                    or 0
                )
            else:
                counts["customer_app_carts"] = rowcount(
                    db.execute(
                        text(f"DELETE FROM dbo.customer_app_carts WHERE {cart_filter}"),
                        {"key": key},
                    )
                )

        if table_exists(db, "CUST_SMS"):
            cust_where = f"""
                (
                    LEN(LTRIM(RTRIM(ISNULL(MOBILE_NO, '')))) >= 10
                    AND {_SQL_RIGHT10.format(col="MOBILE_NO")} = :key
                ) OR (
                    LEN(LTRIM(RTRIM(ISNULL(MOBILE_NO_TMP, '')))) >= 10
                    AND {_SQL_RIGHT10.format(col="MOBILE_NO_TMP")} = :key
                )
            """
            if dry_run:
                counts["CUST_SMS"] = int(
                    db.execute(
                        text(f"SELECT COUNT(1) FROM dbo.CUST_SMS WHERE {cust_where}"),
                        {"key": key},
                    ).scalar()
                    or 0
                )
            else:
                counts["CUST_SMS"] = rowcount(
                    db.execute(
                        text(f"DELETE FROM dbo.CUST_SMS WHERE {cust_where}"),
                        {"key": key},
                    )
                )

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return counts


def get_json(url: str, timeout: float = 8) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def post_json(url: str, payload: dict, timeout: float = 8) -> dict:
    raw = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=raw,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def confirm_apis(mobile_local: str) -> None:
    q = urllib.parse.quote(mobile_local)
    guest_url = f"{ERP_BASE}{API_PREFIX}/public/whatsapp/mobile-otp/status?mobile={q}"
    app_url = f"{ERP_BASE}{API_PREFIX}/public/customer-app/mobile-otp/status?mobile={q}"
    lookup_url = f"{ERP_BASE}{API_PREFIX}/public/customer-app/customers/lookup"
    try:
        guest = get_json(guest_url)
        print(
            "guest_otp required={0} verified={1}".format(
                guest.get("required"),
                guest.get("verified"),
            )
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"guest_otp status skipped ({exc.__class__.__name__})")
    try:
        app = get_json(app_url)
        print(
            "app_otp required={0} verified={1}".format(
                app.get("required"),
                app.get("verified"),
            )
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"app_otp status skipped ({exc.__class__.__name__})")
    try:
        lookup = post_json(lookup_url, {"mobile": mobile_local})
        print(f"customer_lookup exists={lookup.get('exists')}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"customer_lookup skipped ({exc.__class__.__name__})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clear OTP + CUST_SMS for one Pakistan mobile so it can register again.",
    )
    parser.add_argument(
        "mobile",
        help="Pakistan mobile (03XXXXXXXXX, 3XXXXXXXXX, or 92XXXXXXXXXX)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count matching rows/keys only; do not delete.",
    )
    args = parser.parse_args()
    key = parse_mobile(args.mobile)
    ids = variants(key)
    mode = "dry-run" if args.dry_run else "delete"
    print(f"mode={mode}")
    print(
        "mobile_key={key} local={local} e164={e164}".format(**ids)
    )

    pending_n, verified_n = clear_guest_json(key, dry_run=args.dry_run)
    print(f"guest_json pending_removed={pending_n} verified_removed={verified_n}")
    print(f"guest_json file={GUEST_OTP_FILE}")

    sql_counts = clear_sql(key, dry_run=args.dry_run)
    for table, n in sql_counts.items():
        label = "matched" if args.dry_run else "deleted"
        print(f"{table} {label}={n}")

    confirm_apis(ids["local"])


if __name__ == "__main__":
    main()
