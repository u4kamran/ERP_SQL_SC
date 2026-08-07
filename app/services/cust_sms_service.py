"""Service layer for dbo.CUST_SMS CRUD."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.cust_sms_repository import CustSmsRepository
from app.schemas.cust_sms import (
    CustSmsCreate,
    CustSmsListResponse,
    CustSmsResponse,
    CustSmsUpdate,
)


class CustSmsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustSmsRepository(db)

    def list_rows(self, skip: int = 0, limit: int = 50, search: str | None = None) -> CustSmsListResponse:
        q = (search or "").strip()
        total = self.repo.count(search=q)
        rows = self.repo.list_rows(skip=skip, limit=limit, search=q)
        return CustSmsListResponse(
            items=[self._to_response(r) for r in rows],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_row(self, cust_id: int) -> CustSmsResponse:
        row = self.repo.get_by_id(cust_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CUST_SMS record not found.")
        return self._to_response(row)

    def create_row(self, data: CustSmsCreate) -> CustSmsResponse:
        payload = self._payload(data)
        existing = self.repo.find_by_mobile(payload["mobile_no"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mobile {payload['mobile_no']} already exists (CUST_ID {existing['cust_id']}).",
            )
        try:
            cust_id = self.repo.create(payload)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mobile number already exists (unique MOBILE_NO).",
            ) from None
        return self.get_row(cust_id)

    def update_row(self, cust_id: int, data: CustSmsUpdate) -> CustSmsResponse:
        current = self.repo.get_by_id(cust_id)
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CUST_SMS record not found.")

        payload = self._payload(data)
        duplicate = self.repo.find_by_mobile(payload["mobile_no"], exclude_cust_id=cust_id)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mobile {payload['mobile_no']} already used by CUST_ID {duplicate['cust_id']}.",
            )
        try:
            updated = self.repo.update(cust_id, payload)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mobile number conflict (unique MOBILE_NO).",
            ) from None
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CUST_SMS record not found.")
        return self.get_row(cust_id)

    def delete_row(self, cust_id: int) -> None:
        if not self.repo.delete(cust_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CUST_SMS record not found.")

    @staticmethod
    def _payload(data: CustSmsCreate | CustSmsUpdate) -> dict:
        return {
            "cust_name": (data.cust_name or "").strip(),
            "mobile_no": (data.mobile_no or "").strip(),
            "mobile_no_tmp": (data.mobile_no_tmp or None),
            "cust_address": (data.cust_address or None),
            "status": data.status,
            "star_rating": (data.star_rating or None),
            "star_rating_value": (data.star_rating_value or None),
            "star_rating_visit": (data.star_rating_visit or None),
            "star_rating_visit_value": (data.star_rating_visit_value or None),
            "star_rating_tsales": (data.star_rating_tsales or None),
            "star_rating_tsales_value": (data.star_rating_tsales_value or None),
        }

    @staticmethod
    def _to_response(row: dict) -> CustSmsResponse:
        return CustSmsResponse(
            cust_id=int(row["cust_id"]),
            cust_name=str(row.get("cust_name") or ""),
            mobile_no=str(row.get("mobile_no") or ""),
            mobile_no_tmp=str(row.get("mobile_no_tmp") or ""),
            cust_address=str(row.get("cust_address") or ""),
            status=row.get("status"),
            added_datetime=row.get("added_datetime"),
            star_rating=str(row.get("star_rating") or ""),
            star_rating_value=str(row.get("star_rating_value") or ""),
            star_rating_visit=str(row.get("star_rating_visit") or ""),
            star_rating_visit_value=str(row.get("star_rating_visit_value") or ""),
            star_rating_tsales=str(row.get("star_rating_tsales") or ""),
            star_rating_tsales_value=str(row.get("star_rating_tsales_value") or ""),
        )
