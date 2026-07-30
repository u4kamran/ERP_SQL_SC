"""Verify CONTPL migration: roles, preferences, sample login."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text

from app.database.session import SessionLocal
from app.models.role import Role, UserRole
from app.models.user import User, UserPreference
from app.security.password import verify_password
from scripts.migrate_contpl_users import load_contpl_rows


def main() -> None:
    rows = load_contpl_rows()
    db = SessionLocal()
    try:
        users = db.execute(select(User).where(User.IsDeleted == False)).scalars().all()  # noqa: E712
        roles = {
            r.RoleId: r.RoleCode
            for r in db.execute(select(Role)).scalars().all()
        }
        user_roles = db.execute(select(UserRole)).scalars().all()

        print("=" * 70)
        print(f"Active auth users: {len(users)}")
        print(f"CONTPL rows: {len(rows)}")
        print("=" * 70)

        migrated = 0
        with_role = 0
        with_prefs = 0
        password_ok = 0

        contpl_by_id = {int(r["L_uid"]): r for r in rows}

        for user in sorted(users, key=lambda u: u.UserId):
            if user.UserId not in contpl_by_id:
                print(f"EXTRA   UserId {user.UserId:>3}  {user.Username:<18}  (seed/system user)")
                continue

            migrated += 1
            row = contpl_by_id[user.UserId]
            plain = row["P_w"] or ""
            pw_ok = verify_password(plain, user.PasswordHash) if plain else False
            if pw_ok:
                password_ok += 1

            ur = [roles[ur.RoleId] for ur in user_roles if ur.UserId == user.UserId]
            if ur:
                with_role += 1

            prefs = db.execute(
                select(UserPreference).where(UserPreference.UserId == user.UserId)
            ).scalars().all()
            legacy = [p for p in prefs if p.PreferenceKey.startswith("legacy_contpl")]
            if legacy:
                with_prefs += 1

            status = "OK" if pw_ok else "PW?"
            print(
                f"{status:<4}  UserId {user.UserId:>3}  {user.Username:<18}  "
                f"roles={','.join(ur) or '-'}  legacy_prefs={len(legacy)}"
            )

        print("-" * 70)
        print(f"Migrated CONTPL users: {migrated}/{len(rows)}")
        print(f"With role assigned:    {with_role}/{migrated}")
        print(f"With legacy prefs:     {with_prefs}/{migrated}")
        print(f"Password verifies:     {password_ok}/{migrated}")
        print("=" * 70)

        if migrated == len(rows) and with_role == migrated and password_ok == migrated:
            print("ALL CHECKS PASSED - migration complete.")
        else:
            print("Some checks need attention - run: python -m scripts.migrate_contpl_users --update")
    finally:
        db.close()


if __name__ == "__main__":
    main()
