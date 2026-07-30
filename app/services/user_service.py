"""User management business logic."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas import UserCreate, UserUpdate
from app.security.password import hash_password, validate_password_policy


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_user(self, data: UserCreate, created_by: int) -> User:
        if self.user_repo.get_by_username(data.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists.")
        if self.user_repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")

        valid, errors = validate_password_policy(data.password)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(errors))

        user = User(
            Username=data.username,
            Email=data.email,
            PasswordHash=hash_password(data.password),
            FirstName=data.first_name,
            LastName=data.last_name,
            PhoneNumber=data.phone_number,
            MustChangePassword=True,
            PasswordChangedDate=datetime.utcnow(),
            PasswordExpiryDate=datetime.utcnow() + timedelta(days=settings.password_expiry_days),
            CreatedBy=created_by,
        )
        self.user_repo.create(user)
        if data.role_ids:
            self.user_repo.assign_roles(user.UserId, data.role_ids, created_by)

        self.audit_repo.log_audit(
            action="USER_CREATE",
            user_id=created_by,
            entity_type="User",
            entity_id=str(user.UserId),
            new_values=f"username={user.Username}",
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, data: UserUpdate, modified_by: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if data.email and data.email != user.Email:
            if self.user_repo.get_by_email(data.email):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
            user.Email = data.email
        if data.first_name is not None:
            user.FirstName = data.first_name
        if data.last_name is not None:
            user.LastName = data.last_name
        if data.phone_number is not None:
            user.PhoneNumber = data.phone_number
        if data.is_active is not None:
            user.IsActive = data.is_active
        if data.role_ids is not None:
            self.user_repo.set_roles(user_id, data.role_ids, modified_by)

        user.ModifiedBy = modified_by
        self.user_repo.update(user)
        self.audit_repo.log_audit(
            action="USER_UPDATE",
            user_id=modified_by,
            entity_type="User",
            entity_id=str(user_id),
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user or user.IsDeleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    def list_users(self, skip: int = 0, limit: int = 50) -> List[User]:
        return self.user_repo.list_users(skip, limit)

    def soft_delete_user(self, user_id: int, deleted_by: int):
        user = self.get_user(user_id)
        user.IsDeleted = True
        user.IsActive = False
        user.ModifiedBy = deleted_by
        self.user_repo.update(user)
        self.audit_repo.log_audit(
            action="USER_DELETE",
            user_id=deleted_by,
            entity_type="User",
            entity_id=str(user_id),
        )
        self.db.commit()

    def admin_reset_password(
        self,
        user_id: int,
        new_password: str,
        modified_by: int,
        must_change_password: bool = True,
    ) -> User:
        user = self.get_user(user_id)
        valid, errors = validate_password_policy(new_password)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(errors))

        self.user_repo.add_password_history(user_id, user.PasswordHash)
        user.PasswordHash = hash_password(new_password)
        user.PasswordChangedDate = datetime.utcnow()
        user.PasswordExpiryDate = datetime.utcnow() + timedelta(days=settings.password_expiry_days)
        user.MustChangePassword = must_change_password
        user.ModifiedBy = modified_by
        self.user_repo.update(user)
        self.audit_repo.log_audit(
            action="ADMIN_PASSWORD_RESET",
            user_id=modified_by,
            entity_type="User",
            entity_id=str(user_id),
        )
        self.db.commit()
        self.db.refresh(user)
        return user
