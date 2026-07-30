"""
Migrate legacy users from dbo.CONTPL (nsds2626) into auth.Users (NSDS2626_AUTH).

Preserves:
  - L_uid  -> UserId (same numeric ID)
  - l_id   -> Username (login name)
  - P_w    -> Password (re-hashed with BCrypt; same plain password works at login)
  - full_name -> FirstName / LastName

Run:
  python -m scripts.migrate_contpl_users
  python -m scripts.migrate_contpl_users --update   # refresh passwords for existing users
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text

from app.database.business_session import business_engine
from app.database.session import SessionLocal
from app.models.role import Role, UserRole
from app.models.user import User, UserPreference
from app.security.password import hash_password


def split_name(full_name: str | None) -> tuple[str | None, str | None]:
    if not full_name:
        return None, None
    parts = full_name.strip().split(None, 1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


def resolve_role_code(username: str, full_name: str | None) -> str:
    name = (full_name or "").lower()
    user = username.lower()
    if user in {"sa", "admin", "administrator"} or "administrator" in name:
        return "SUPER_ADMIN"
    return "USER"


def load_contpl_rows() -> list[dict]:
    with business_engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    L_uid,
                    LTRIM(RTRIM(l_id)) AS l_id,
                    LTRIM(RTRIM(P_w)) AS P_w,
                    LTRIM(RTRIM(full_name)) AS full_name,
                    r_str,
                    dt_create,
                    dt_exp
                FROM dbo.CONTPL
                WHERE l_id IS NOT NULL AND LTRIM(RTRIM(l_id)) <> ''
                ORDER BY L_uid
                """
            )
        ).mappings().all()
    return [dict(r) for r in rows]


def upsert_preference(db, user_id: int, key: str, value: str) -> None:
    pref = db.execute(
        select(UserPreference).where(
            UserPreference.UserId == user_id,
            UserPreference.PreferenceKey == key,
        )
    ).scalar_one_or_none()
    if pref:
        pref.PreferenceValue = value
        pref.ModifiedDate = datetime.utcnow()
    else:
        db.add(
            UserPreference(
                UserId=user_id,
                PreferenceKey=key,
                PreferenceValue=value,
                IsActive=True,
            )
        )


def migrate(update_existing: bool = False) -> None:
    rows = load_contpl_rows()
    if not rows:
        print("No rows found in dbo.CONTPL.")
        return

    db = SessionLocal()
    created = updated = skipped = 0

    try:
        roles = {
            r.RoleCode: r
            for r in db.execute(select(Role).where(Role.IsDeleted == False)).scalars().all()  # noqa: E712
        }

        for row in rows:
            legacy_id = int(row["L_uid"])
            username = row["l_id"]
            plain_password = row["P_w"] or ""
            first_name, last_name = split_name(row.get("full_name"))
            email = f"{username.lower()}@ahsteellab.com"
            role_code = resolve_role_code(username, row.get("full_name"))
            password_hash = hash_password(plain_password) if plain_password else hash_password("ChangeMe@2026!")

            existing = db.execute(
                select(User).where(
                    (User.UserId == legacy_id) | (User.Username == username)
                )
            ).scalar_one_or_none()

            if existing:
                if not update_existing:
                    print(f"SKIP  {username} (UserId {legacy_id}) - already exists")
                    skipped += 1
                    continue

                existing.Username = username
                existing.Email = email
                existing.PasswordHash = password_hash
                existing.FirstName = first_name
                existing.LastName = last_name
                existing.PasswordExpiryDate = row.get("dt_exp")
                existing.MustChangePassword = False
                existing.IsActive = True
                existing.IsDeleted = False
                existing.ModifiedDate = datetime.utcnow()
                user_id = existing.UserId
                updated += 1
                print(f"UPDATE {username} (UserId {user_id})")
            else:
                db.execute(text("SET IDENTITY_INSERT auth.Users ON"))
                db.execute(
                    text(
                        """
                        INSERT INTO auth.Users (
                            UserId, Username, Email, PasswordHash,
                            FirstName, LastName,
                            MustChangePassword, PasswordChangedDate, PasswordExpiryDate,
                            FailedLoginAttempts, IsEmailVerified,
                            IsActive, IsDeleted, CreatedDate
                        ) VALUES (
                            :user_id, :username, :email, :password_hash,
                            :first_name, :last_name,
                            0, GETUTCDATE(), :password_expiry,
                            0, 1,
                            1, 0, :created_date
                        )
                        """
                    ),
                    {
                        "user_id": legacy_id,
                        "username": username,
                        "email": email,
                        "password_hash": password_hash,
                        "first_name": first_name,
                        "last_name": last_name,
                        "password_expiry": row.get("dt_exp"),
                        "created_date": row.get("dt_create") or datetime.utcnow(),
                    },
                )
                db.execute(text("SET IDENTITY_INSERT auth.Users OFF"))
                user_id = legacy_id
                created += 1
                print(f"CREATE {username} (UserId {user_id})")

            role = roles.get(role_code)
            if role:
                has_role = db.execute(
                    select(UserRole).where(
                        UserRole.UserId == user_id,
                        UserRole.RoleId == role.RoleId,
                    )
                ).scalar_one_or_none()
                if not has_role:
                    db.add(UserRole(UserId=user_id, RoleId=role.RoleId, CreatedBy=user_id))

            if row.get("r_str"):
                upsert_preference(db, user_id, "legacy_contpl_r_str", str(row["r_str"]))
            upsert_preference(db, user_id, "legacy_contpl_uid", str(legacy_id))

        db.commit()
        print("")
        print(f"Done. Created: {created}, Updated: {updated}, Skipped: {skipped}")
        print("Users can log in with the same username and password from CONTPL.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate dbo.CONTPL users to auth.Users")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update passwords/details for users that already exist",
    )
    args = parser.parse_args()
    migrate(update_existing=args.update)


if __name__ == "__main__":
    main()
