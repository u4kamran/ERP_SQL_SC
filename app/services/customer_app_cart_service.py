"""Customer App Cart business logic — saved basket, not a sales invoice."""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.customer_app_cart_repository import CustomerAppCartRepository
from app.schemas.customer_app_cart import (
    CartDetailOut,
    CartLineOut,
    CartListPage,
    CartSummaryOut,
    CustomerLookupResponse,
    CustomerRegisterRequest,
    CustomerRegisterResponse,
    SaveCartRequest,
    SaveCartResponse,
)
from app.schemas.public_catalog import CartValidateLineIn, CartValidateRequest
from app.services.customer_app_otp_service import CustomerAppOtpService
from app.services.public_catalog_service import PublicCatalogService


ALLOWED_STAFF_TRANSITIONS: dict[str, set[str]] = {
    "SAVED": {"UNDER_REVIEW", "CONTACTED", "CONFIRMED", "CANCELLED"},
    "UNDER_REVIEW": {"CONTACTED", "CONFIRMED", "CANCELLED"},
    "CONTACTED": {"CONFIRMED", "CANCELLED", "UNDER_REVIEW"},
    "CONFIRMED": {"CANCELLED"},
    "CONVERTED": set(),
    "CANCELLED": set(),
    "EXPIRED": set(),
}


class CustomerAppCartService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerAppCartRepository(db)
        self.catalog = PublicCatalogService(db)
        self.otp = CustomerAppOtpService(db)

    @staticmethod
    def mobile_key(value: str) -> str:
        digits = re.sub(r"\D", "", value or "")
        if len(digits) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Enter a valid mobile number with at least 10 digits (03XXXXXXXXX).",
            )
        return digits[-10:]

    @staticmethod
    def mobile_for_storage(value: str) -> str:
        digits = re.sub(r"\D", "", value or "")
        if digits.startswith("92") and len(digits) >= 12:
            return "0" + digits[2:12]
        if len(digits) >= 11 and digits.startswith("0"):
            return digits[:11]
        if len(digits) >= 10:
            return "0" + digits[-10:]
        return digits

    def require_verified_mobile(self, mobile: str) -> None:
        self.otp.require_verified(mobile)

    def lookup_customer(self, mobile: str) -> CustomerLookupResponse:
        key = self.mobile_key(mobile)
        row = self.repo.find_customer_by_mobile_key(key)
        if not row:
            return CustomerLookupResponse(
                exists=False,
                message="No customer found for this mobile. Please register.",
            )
        return CustomerLookupResponse(
            exists=True,
            cust_id=int(row["cust_id"]),
            cust_name=row.get("cust_name") or "",
            mobile_no=row.get("mobile_no") or self.mobile_for_storage(mobile),
            cust_address=row.get("cust_address") or None,
            message="Customer already registered. Please continue with your existing account.",
        )

    def register_customer(self, payload: CustomerRegisterRequest) -> CustomerRegisterResponse:
        self.require_verified_mobile(payload.mobile)
        key = self.mobile_key(payload.mobile)
        storage = self.mobile_for_storage(payload.mobile)
        existing = self.repo.find_customer_by_mobile_key(key)
        if existing:
            return CustomerRegisterResponse(
                created=False,
                cust_id=int(existing["cust_id"]),
                cust_name=existing.get("cust_name") or payload.cust_name.strip(),
                mobile_no=existing.get("mobile_no") or storage,
                cust_address=existing.get("cust_address") or payload.cust_address,
                message="Customer already registered. Please continue with your existing account.",
            )
        name = payload.cust_name.strip()
        if len(name) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Customer name is required.",
            )
        try:
            cust_id = self.repo.create_customer(
                name=name,
                mobile=storage,
                address=(payload.cust_address or "").strip() or None,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return CustomerRegisterResponse(
            created=True,
            cust_id=cust_id,
            cust_name=name,
            mobile_no=storage,
            cust_address=(payload.cust_address or "").strip() or None,
            message="Customer registered successfully.",
        )

    def save_cart(self, payload: SaveCartRequest) -> SaveCartResponse:
        self.require_verified_mobile(payload.mobile)
        key = self.mobile_key(payload.mobile)
        storage = self.mobile_for_storage(payload.mobile)
        idem = payload.idempotency_key.strip()
        if len(idem) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid idempotency key.",
            )

        existing_cart = self.repo.get_by_idempotency(idem)
        if existing_cart:
            detail = self._detail_from_header(existing_cart)
            return SaveCartResponse(
                cart=detail,
                customer_created=False,
                message="Cart already saved (duplicate request ignored).",
            )

        validation = self.catalog.validate_cart(
            CartValidateRequest(
                lines=[CartValidateLineIn(manual_id=l.manual_id, qty=l.qty) for l in payload.lines]
            )
        )
        ok_lines = [ln for ln in validation.lines if ln.ok and ln.unit_price > 0 and ln.qty > 0]
        if not ok_lines:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=validation.message
                or "No valid products remain in the cart. Please review prices and stock.",
            )

        name = payload.cust_name.strip()
        address = (payload.cust_address or "").strip() or None
        customer_created = False
        customer = self.repo.find_customer_by_mobile_key(key)
        try:
            if customer:
                cust_id = int(customer["cust_id"])
                if not name:
                    name = (customer.get("cust_name") or "").strip()
                if not address:
                    address = (customer.get("cust_address") or "").strip() or None
            else:
                if len(name) < 2:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Customer name is required to register and save the cart.",
                    )
                cust_id = self.repo.create_customer(name=name, mobile=storage, address=address)
                customer_created = True

            cart_ref = self.repo.next_cart_ref()
            subtotal = round(sum(float(ln.line_total) for ln in ok_lines), 2)
            tax = round(sum(float(ln.gst_amount or 0) * float(ln.qty) for ln in ok_lines), 2)
            cart_id = self.repo.insert_cart(
                cart_ref=cart_ref,
                cust_sms_id=cust_id,
                customer_name=name,
                customer_mobile_no=storage,
                mobile_key=key,
                customer_address=address,
                total_items=len(ok_lines),
                estimated_subtotal=subtotal,
                estimated_discount=0.0,
                estimated_tax=tax,
                estimated_total=subtotal,
                idempotency_key=idem,
            )
            for idx, ln in enumerate(ok_lines, start=1):
                self.repo.insert_line(
                    cart_id=cart_id,
                    line_no=idx,
                    line={
                        "manual_id": ln.manual_id,
                        "item_title": ln.item_title or f"Item {ln.manual_id}",
                        "barcode": ln.barcodeid,
                        "uom_title": ln.uom_title,
                        "qty": float(ln.qty),
                        "unit_price": float(ln.unit_price),
                        "discount_amount": 0.0,
                        "tax_amount": float(ln.gst_amount or 0) * float(ln.qty),
                        "line_total": float(ln.line_total),
                    },
                )
            self.repo.insert_history(
                cart_id=cart_id,
                old_status=None,
                new_status="SAVED",
                action_code="CART_CREATED",
                actor_username=f"customer:{storage}",
                remarks="Saved from MOBILE_APP",
            )
            self.db.commit()
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            # Concurrent duplicate idempotency
            raced = self.repo.get_by_idempotency(idem)
            if raced:
                return SaveCartResponse(
                    cart=self._detail_from_header(raced),
                    customer_created=False,
                    message="Cart already saved (duplicate request ignored).",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not save cart. Please try again. ({exc})",
            ) from exc

        header = self.repo.get_by_id(cart_id)
        assert header is not None
        return SaveCartResponse(
            cart=self._detail_from_header(header),
            customer_created=customer_created,
            message=f"Cart saved successfully. Reference {header['cart_ref']}.",
        )

    def list_my_carts(self, *, mobile: str, page: int = 1, page_size: int = 20) -> CartListPage:
        self.require_verified_mobile(mobile)
        key = self.mobile_key(mobile)
        page = max(page, 1)
        page_size = min(max(page_size, 1), 50)
        total = self.repo.count_carts(mobile_key=key)
        rows = self.repo.list_carts(
            skip=(page - 1) * page_size,
            limit=page_size,
            mobile_key=key,
        )
        return CartListPage(
            items=[self._summary(r) for r in rows],
            page=page,
            page_size=page_size,
            total=total,
            has_more=(page * page_size) < total,
        )

    def get_my_cart(self, *, cart_ref: str, mobile: str) -> CartDetailOut:
        self.require_verified_mobile(mobile)
        key = self.mobile_key(mobile)
        header = self.repo.get_by_ref(cart_ref)
        if not header or header.get("mobile_key") != key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
        return self._detail_from_header(header)

    def staff_list(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        status_filter: str | None = None,
        source: str | None = "MOBILE_APP",
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> CartListPage:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        total = self.repo.count_carts(
            status=status_filter or None,
            source=source or None,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        rows = self.repo.list_carts(
            skip=(page - 1) * page_size,
            limit=page_size,
            status=status_filter or None,
            source=source or None,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
        return CartListPage(
            items=[self._summary(r) for r in rows],
            page=page,
            page_size=page_size,
            total=total,
            has_more=(page * page_size) < total,
        )

    def staff_get(self, cart_id: int) -> CartDetailOut:
        header = self.repo.get_by_id(cart_id)
        if not header:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
        return self._detail_from_header(header, include_history=True)

    def staff_update_status(
        self,
        *,
        cart_id: int,
        new_status: str,
        actor_username: str,
        remarks: str | None = None,
        allow_cancel: bool = True,
    ) -> CartDetailOut:
        header = self.repo.get_by_id(cart_id)
        if not header:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
        old = str(header["status"])
        if new_status == old:
            return self._detail_from_header(header, include_history=True)
        if new_status == "CANCELLED" and not allow_cancel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to cancel carts.",
            )
        if new_status == "CONVERTED":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Convert to sales order is not available yet. Use status Confirm for now.",
            )
        allowed = ALLOWED_STAFF_TRANSITIONS.get(old, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot change status from {old} to {new_status}.",
            )
        action = {
            "UNDER_REVIEW": "STATUS_UNDER_REVIEW",
            "CONTACTED": "STATUS_CONTACTED",
            "CONFIRMED": "STATUS_CONFIRMED",
            "CANCELLED": "CART_CANCELLED",
        }.get(new_status, "STATUS_CHANGED")
        try:
            self.repo.update_status(cart_id, new_status)
            self.repo.insert_history(
                cart_id=cart_id,
                old_status=old,
                new_status=new_status,
                action_code=action,
                actor_username=actor_username,
                remarks=remarks,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.staff_get(cart_id)

    def staff_convert_stub(self, cart_id: int) -> None:
        header = self.repo.get_by_id(cart_id)
        if not header:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
        if header["status"] == "CONVERTED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This cart was already converted.",
            )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Convert to ERP sales order is prepared for Phase 2. "
                "There is no public/web sales-invoice create API yet — "
                "staff must use the existing ERP sales workflow. "
                "Saving a cart never creates a sales invoice."
            ),
        )

    def _summary(self, row: dict[str, Any]) -> CartSummaryOut:
        return CartSummaryOut(
            id=int(row["id"]),
            cart_ref=row["cart_ref"],
            cust_sms_id=int(row["cust_sms_id"]),
            customer_name=row.get("customer_name") or "",
            customer_mobile_no=row.get("customer_mobile_no") or "",
            customer_address=(row.get("customer_address") or None) or None,
            status=row["status"],
            source=row.get("source") or "MOBILE_APP",
            total_items=int(row.get("total_items") or 0),
            estimated_subtotal=float(row.get("estimated_subtotal") or 0),
            estimated_discount=float(row.get("estimated_discount") or 0),
            estimated_tax=float(row.get("estimated_tax") or 0),
            estimated_total=float(row.get("estimated_total") or 0),
            converted_doc_ref=row.get("converted_doc_ref"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _detail_from_header(
        self, header: dict[str, Any], *, include_history: bool = False
    ) -> CartDetailOut:
        cart_id = int(header["id"])
        lines = [
            CartLineOut(
                line_no=int(ln["line_no"]),
                manual_id=int(ln["manual_id"]),
                item_title=ln.get("item_title") or "",
                barcode=(ln.get("barcode") or None) or None,
                uom_title=(ln.get("uom_title") or None) or None,
                qty=float(ln["qty"]),
                unit_price=float(ln["unit_price"]),
                discount_amount=float(ln.get("discount_amount") or 0),
                tax_amount=float(ln.get("tax_amount") or 0),
                line_total=float(ln["line_total"]),
            )
            for ln in self.repo.list_lines(cart_id)
        ]
        history: list[dict] = []
        if include_history:
            history = self.repo.list_history(cart_id)
        base = self._summary(header)
        return CartDetailOut(**base.model_dump(), lines=lines, history=history)
