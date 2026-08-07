"""Business rules and transaction boundaries for delivery management."""

from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.delivery_repository import DeliveryRepository
from app.schemas.delivery import (
    DeliveryAssignRequest,
    DeliveryBulkActionResponse,
    DeliveryBulkDeliverRequest,
    DeliveryCustomerLookup,
    DeliveryOrderListResponse,
    DeliveryOrderResponse,
    DeliveryRiderCreate,
    DeliveryRiderResponse,
    DeliveryRiderUpdate,
    DeliveryRegistrationInvoice,
    DeliveryRegistrationRequest,
    DeliveryRegistrationResponse,
    DeliveryStatusUpdateRequest,
    DeliverySummaryResponse,
    DeliverySyncResponse,
)


_ALL_STATUSES = (
    "Pending",
    "Assigned",
    "On The Way",
    "Arrived",
    "Delivered",
    "Cancelled",
    "Failed Delivery",
    "Returned",
)

_ASSIGNABLE_STATUSES = {"Pending", "Assigned", "Failed Delivery"}


class DeliveryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DeliveryRepository(db)

    def summary(self) -> DeliverySummaryResponse:
        result = self.repo.summary()
        counts = {name: 0 for name in _ALL_STATUSES}
        counts.update(result["status_counts"])
        result["status_counts"] = counts
        return DeliverySummaryResponse(**result)

    def list_orders(
        self,
        *,
        skip: int,
        limit: int,
        search: str,
        order_status: str | None,
        rider_id: int | None,
    ) -> DeliveryOrderListResponse:
        total = self.repo.count_orders(
            search=search, order_status=order_status, rider_id=rider_id
        )
        rows = self.repo.list_orders(
            skip=skip,
            limit=limit,
            search=search,
            order_status=order_status,
            rider_id=rider_id,
        )
        return DeliveryOrderListResponse(
            items=[DeliveryOrderResponse(**row) for row in rows],
            total=total,
            skip=skip,
            limit=limit,
        )

    def search_registration_invoices(
        self,
        *,
        gp_time: str,
    ) -> list[DeliveryRegistrationInvoice]:
        value = (gp_time or "").strip()
        if not value:
            return []
        return [
            DeliveryRegistrationInvoice(**row)
            for row in self.repo.search_registration_invoices(
                gp_time=value,
                limit=20,
            )
        ]

    def lookup_delivery_customer(self, mobile: str) -> DeliveryCustomerLookup:
        value = (mobile or "").strip()
        mobile_key = self._mobile_key(value)
        customer = self.repo.find_delivery_customer(mobile_key)
        if not customer:
            return DeliveryCustomerLookup(exists=False, mobile=value)
        return DeliveryCustomerLookup(exists=True, **customer)

    def register_invoice(
        self,
        data: DeliveryRegistrationRequest,
        *,
        actor_username: str,
    ) -> DeliveryRegistrationResponse:
        invoice = self.repo.get_registration_invoice(data.source_serial_no)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice was not found.",
            )

        mobile = data.mobile.strip()
        mobile_key = self._mobile_key(mobile)
        current_mobile = str(invoice.get("current_mobile") or "").strip()
        if current_mobile not in {"", "."}:
            current_key = self._mobile_key(current_mobile)
            if current_key != mobile_key:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "This invoice is already registered with another proper "
                        "mobile number."
                    ),
                )

        customer = self.repo.find_delivery_customer(mobile_key)
        customer_created = customer is None
        try:
            if customer is None:
                cust_sms_id = self.repo.create_delivery_customer(
                    name=data.name.strip(),
                    mobile=mobile,
                    address=data.address.strip(),
                )
            else:
                cust_sms_id = int(customer["cust_sms_id"])

            if not self.repo.update_invoice_delivery_mobile(
                source_serial_no=data.source_serial_no,
                mobile=mobile,
            ):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invoice was not found while saving the mobile number.",
                )

            delivery_order_id = self.repo.get_order_id_by_source(
                data.source_serial_no
            )
            if delivery_order_id is not None:
                self.repo.refresh_source_orders()
            else:
                source = self.repo.source_invoice_by_serial(data.source_serial_no)
                if not source:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Invoice could not be converted into a delivery order.",
                    )
                delivery_order_id = self.repo.insert_source_order(source)
                if delivery_order_id is None:
                    delivery_order_id = self.repo.get_order_id_by_source(
                        data.source_serial_no
                    )
                if delivery_order_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Delivery order could not be created.",
                    )
                self.repo.add_history(
                    order_id=delivery_order_id,
                    old_status=None,
                    new_status="Pending",
                    actor_username=actor_username,
                    remarks="Registered from QR/GP_TIME delivery page.",
                )

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return DeliveryRegistrationResponse(
            delivery_order_id=delivery_order_id,
            invoice_id=int(invoice["invoice_id"]),
            customer_created=customer_created,
            cust_sms_id=cust_sms_id,
            message="Invoice registered for delivery successfully.",
        )

    def sync(
        self, *, lookback_hours: int, limit: int, actor_username: str
    ) -> DeliverySyncResponse:
        created = 0
        try:
            refreshed = self.repo.refresh_source_orders()
            self.repo.enrich_customer_contacts()
            sources = self.repo.source_invoices(
                lookback_hours=lookback_hours, limit=limit
            )
            for source in sources:
                order_id = self.repo.insert_source_order(source)
                if order_id is None:
                    continue
                self.repo.add_history(
                    order_id=order_id,
                    old_status=None,
                    new_status="Pending",
                    actor_username=actor_username,
                    remarks="Imported from FIN_INV_M.",
                )
                created += 1
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return DeliverySyncResponse(
            lookback_hours=lookback_hours,
            limit=limit,
            scanned=len(sources),
            created=created,
            refreshed=refreshed,
            skipped=len(sources) - created,
        )

    def list_riders(self) -> list[DeliveryRiderResponse]:
        return [
            DeliveryRiderResponse(**row) for row in self.repo.list_riders()
        ]

    def create_rider(self, data: DeliveryRiderCreate) -> DeliveryRiderResponse:
        try:
            rider_id = self.repo.create_rider(name=data.name, phone=data.phone)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        rider = self.repo.get_rider(rider_id)
        if not rider:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rider was created but could not be loaded.",
            )
        return DeliveryRiderResponse(**rider)

    def update_rider(
        self,
        rider_id: int,
        data: DeliveryRiderUpdate,
    ) -> DeliveryRiderResponse:
        self._require_rider(rider_id)
        try:
            self.repo.update_rider(
                rider_id=rider_id,
                name=data.name,
                phone=data.phone,
                is_active=data.is_active,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return DeliveryRiderResponse(**self._require_rider(rider_id))

    def set_rider_active(
        self,
        rider_id: int,
        *,
        is_active: bool,
    ) -> DeliveryRiderResponse:
        self._require_rider(rider_id)
        try:
            self.repo.set_rider_active(rider_id=rider_id, is_active=is_active)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return DeliveryRiderResponse(**self._require_rider(rider_id))

    def assign_order(
        self,
        order_id: int,
        data: DeliveryAssignRequest,
        *,
        actor_username: str,
    ) -> DeliveryOrderResponse:
        order = self._require_order(order_id)
        rider = self.repo.get_rider(data.rider_id)
        if not rider or not bool(rider["is_active"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active rider is required.",
            )
        if order["status"] not in _ASSIGNABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Orders in {order['status']} status cannot be assigned.",
            )

        try:
            self.repo.assign_order(order_id=order_id, rider_id=data.rider_id)
            self.repo.add_history(
                order_id=order_id,
                old_status=str(order["status"]),
                new_status="Assigned",
                actor_username=actor_username,
                remarks=f"Assigned to rider {rider['name']}.",
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return DeliveryOrderResponse(**self._require_order(order_id))

    def bulk_assign_orders(
        self,
        data: DeliveryAssignRequest,
        *,
        actor_username: str,
    ) -> DeliveryBulkActionResponse:
        rider = self.repo.get_rider(data.rider_id)
        if not rider or not bool(rider["is_active"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active rider is required.",
            )
        try:
            changed = self.repo.bulk_assign_orders(rider_id=data.rider_id)
            for item in changed:
                self.repo.add_history(
                    order_id=int(item["order_id"]),
                    old_status=str(item["old_status"]),
                    new_status="Assigned",
                    actor_username=actor_username,
                    remarks=f"Admin bulk-assigned to rider {rider['name']}.",
                )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return DeliveryBulkActionResponse(
            updated=len(changed),
            message=f"{len(changed)} delivery order(s) assigned to {rider['name']}.",
        )

    def bulk_deliver_assigned_orders(
        self,
        data: DeliveryBulkDeliverRequest,
        *,
        actor_username: str,
    ) -> DeliveryBulkActionResponse:
        rider = None
        if data.rider_id is not None:
            rider = self.repo.get_rider(data.rider_id)
            if not rider:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Delivery rider not found.",
                )
        try:
            changed = self.repo.bulk_deliver_assigned_orders(
                rider_id=data.rider_id
            )
            scope = (
                f" for rider {rider['name']}" if rider is not None else ""
            )
            for item in changed:
                self.repo.add_history(
                    order_id=int(item["order_id"]),
                    old_status=str(item["old_status"]),
                    new_status="Delivered",
                    actor_username=actor_username,
                    remarks=f"Admin bulk delivered without GPS{scope}.",
                )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return DeliveryBulkActionResponse(
            updated=len(changed),
            message=f"{len(changed)} assigned order(s){scope} marked Delivered.",
        )

    def update_status(
        self,
        order_id: int,
        data: DeliveryStatusUpdateRequest,
        *,
        actor_username: str,
    ) -> DeliveryOrderResponse:
        order = self._require_order(order_id)
        old_status = str(order["status"])
        new_status = data.status
        if new_status == old_status:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Delivery is already in {new_status} status.",
            )
        if new_status in {"Assigned", "On The Way", "Arrived", "Delivered"} and not order.get(
            "rider_id"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assign a rider before progressing this delivery.",
            )
        if new_status == "Delivered" and (
            data.latitude is None or data.longitude is None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude and longitude are required for Delivered status.",
            )
        if (data.latitude is None) != (data.longitude is None):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude and longitude must be provided together.",
            )

        try:
            self.repo.update_order_status(
                order_id=order_id,
                new_status=new_status,
                latitude=data.latitude,
                longitude=data.longitude,
                accuracy=data.accuracy,
                remarks=data.remarks,
            )
            if data.latitude is not None and order.get("rider_id"):
                self.repo.upsert_rider_location(
                    rider_id=int(order["rider_id"]),
                    order_id=order_id,
                    latitude=data.latitude,
                    longitude=data.longitude,
                    accuracy=data.accuracy,
                    actor_username=actor_username,
                )
            if new_status == "Delivered":
                mobile_key = self._mobile_key(str(order["customer_mobile_no"]))
                self.repo.upsert_customer_location(
                    mobile_key=mobile_key,
                    customer_mobile_no=str(order["customer_mobile_no"]),
                    cust_sms_id=order.get("cust_sms_id"),
                    latitude=data.latitude,
                    longitude=data.longitude,
                    accuracy=data.accuracy,
                    actor_username=actor_username,
                )
            self.repo.add_history(
                order_id=order_id,
                old_status=old_status,
                new_status=new_status,
                actor_username=actor_username,
                remarks=data.remarks,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return DeliveryOrderResponse(**self._require_order(order_id))

    def _require_rider(self, rider_id: int) -> dict:
        rider = self.repo.get_rider(rider_id)
        if not rider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery rider not found.",
            )
        return rider

    @staticmethod
    def _mobile_key(value: str) -> str:
        digits = re.sub(r"\D", "", value or "")
        if len(digits) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Enter a proper customer mobile number with at least 10 digits.",
            )
        return digits[-10:]

    def _require_order(self, order_id: int) -> dict:
        order = self.repo.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery order not found.",
            )
        return order
