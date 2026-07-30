"""Preview CONTPL -> auth.Users sync plan (no changes applied)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text

from app.database.business_session import business_engine
from app.database.session import SessionLocal
from app.models.user import User
from scripts.migrate_contpl_users import load_contpl_rows, resolve_role_code


def preview() -> dict[str, int]:
    rows = load_contpl_rows()
    db = SessionLocal()
    try:
        auth_users = {u.UserId: u for u in db.execute(select(User)).scalars().all()}
        auth_by_name = {u.Username.lower(): u for u in auth_users.values()}
    finally:
        db.close()

    counts = {"create": 0, "skip": 0, "conflict": 0}

    print("=" * 95)
    print(f"CONTPL users (business DB): {len(rows)}")
    print(f"Auth users (NSDS2626_AUTH): {len(auth_users)}")
    print("=" * 95)
    print(
        f"{'Action':<10} {'UID':<6} {'Username':<18} {'Full Name':<22} "
        f"{'r_str':<8} {'Role':<6} {'Details'}"
    )
    print("-" * 95)

    for row in rows:
        uid = int(row["L_uid"])
        username = row["l_id"]
        full_name = row.get("full_name") or ""
        r_str = (row.get("r_str") or "").strip()
        role = resolve_role_code(username, full_name)
        pw_len = len(row.get("P_w") or "")

        by_id = auth_users.get(uid)
        by_name = auth_by_name.get(username.lower())
        existing = by_id or by_name

        if existing and existing.UserId == uid and existing.Username == username:
            action = "SKIP"
            details = f"already in auth (UserId {existing.UserId})"
            counts["skip"] += 1
        elif existing:
            action = "CONFLICT"
            details = (
                f"auth has UserId {existing.UserId}, username '{existing.Username}'"
            )
            counts["conflict"] += 1
        else:
            action = "CREATE"
            details = f"new -> role {role}, pw_len={pw_len}"
            counts["create"] += 1

        print(
            f"{action:<10} {uid:<6} {username:<18} {full_name[:21]:<22} "
            f"{r_str[:7]:<8} {role:<6} {details}"
        )

    print("-" * 95)
    print(
        f"Plan: CREATE={counts['create']}, SKIP={counts['skip']}, "
        f"CONFLICT={counts['conflict']}"
    )
    print("")
    print("To apply new users only:")
    print("  python -m scripts.migrate_contpl_users")
    print("To also refresh existing users (passwords/details):")
    print("  python -m scripts.migrate_contpl_users --update")
    return counts


if __name__ == "__main__":
    preview()
