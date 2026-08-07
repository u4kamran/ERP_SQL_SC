"""Validation and atomic CUST_SMS import for reviewed OCR records."""

import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.customer_import_repository import CustomerImportRepository
from app.schemas.customer_import import (
    CustomerImportFinalizeRequest,
    CustomerImportFinalizeResponse,
)


class CustomerImportService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerImportRepository(db)

    def finalize(
        self,
        data: CustomerImportFinalizeRequest,
    ) -> CustomerImportFinalizeResponse:
        created_ids: list[int] = []
        existing_mobiles: list[str] = []
        seen_keys: set[str] = set()

        try:
            for record in data.records:
                mobile, mobile_key = self._normalize_mobile(record.mobile)
                if mobile_key in seen_keys:
                    existing_mobiles.append(mobile)
                    continue
                seen_keys.add(mobile_key)

                if self.repo.find_by_mobile_key(mobile_key):
                    existing_mobiles.append(mobile)
                    continue

                address = (
                    record.english_address.strip()
                    or record.original_address.strip()
                )
                if not address:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Address is required for mobile {mobile}.",
                    )

                created_ids.append(
                    self.repo.create_customer(
                        name=record.name.strip(),
                        mobile=mobile,
                        address=address,
                    )
                )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return CustomerImportFinalizeResponse(
            received=len(data.records),
            created=len(created_ids),
            skipped_existing=len(existing_mobiles),
            created_ids=created_ids,
            existing_mobiles=existing_mobiles,
            message=(
                f"{len(created_ids)} customer(s) added to CUST_SMS; "
                f"{len(existing_mobiles)} existing or duplicate mobile(s) skipped."
            ),
        )

    @staticmethod
    def _normalize_mobile(value: str) -> tuple[str, str]:
        digits = re.sub(r"\D", "", value or "")
        if digits.startswith("0092"):
            digits = digits[2:]
        if digits.startswith("92"):
            national = digits[2:]
        elif digits.startswith("0"):
            national = digits[1:]
        else:
            national = digits
        if len(national) != 10 or not national.startswith("3"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid Pakistan mobile number: {value}",
            )
        return f"+92{national}", national
