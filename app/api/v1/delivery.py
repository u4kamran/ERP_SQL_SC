"""FastAPI endpoints for the delivery-management proof of concept."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
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
    DeliveryStatus,
    DeliveryStatusUpdateRequest,
    DeliverySummaryResponse,
    DeliverySyncResponse,
)
from app.services.delivery_service import DeliveryService


router = APIRouter()


@router.get(
    "/registration/invoices",
    response_model=list[DeliveryRegistrationInvoice],
)
def search_registration_invoices(
    gp_time: str = Query(..., min_length=1, max_length=200),
    _user: CurrentUser = Depends(require_permission("delivery.orders.update")),
    db: Session = Depends(get_business_db),
) -> list[DeliveryRegistrationInvoice]:
    return DeliveryService(db).search_registration_invoices(gp_time=gp_time)


@router.get(
    "/registration/customer",
    response_model=DeliveryCustomerLookup,
)
def lookup_registration_customer(
    mobile: str = Query(..., min_length=7, max_length=30),
    _user: CurrentUser = Depends(require_permission("delivery.orders.update")),
    db: Session = Depends(get_business_db),
) -> DeliveryCustomerLookup:
    return DeliveryService(db).lookup_delivery_customer(mobile)


@router.post(
    "/registration",
    response_model=DeliveryRegistrationResponse,
)
def register_invoice_for_delivery(
    body: DeliveryRegistrationRequest,
    current_user: CurrentUser = Depends(
        require_permission("delivery.orders.update")
    ),
    db: Session = Depends(get_business_db),
) -> DeliveryRegistrationResponse:
    return DeliveryService(db).register_invoice(
        body,
        actor_username=current_user.username,
    )


@router.get("/summary", response_model=DeliverySummaryResponse)
def get_summary(
    _user: CurrentUser = Depends(require_permission("delivery.orders.view")),
    db: Session = Depends(get_business_db),
) -> DeliverySummaryResponse:
    return DeliveryService(db).summary()


@router.get("/orders", response_model=DeliveryOrderListResponse)
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str = Query("", max_length=100),
    order_status: DeliveryStatus | None = Query(None, alias="status"),
    rider_id: int | None = Query(None, gt=0),
    _user: CurrentUser = Depends(require_permission("delivery.orders.view")),
    db: Session = Depends(get_business_db),
) -> DeliveryOrderListResponse:
    return DeliveryService(db).list_orders(
        skip=skip,
        limit=limit,
        search=search,
        order_status=order_status,
        rider_id=rider_id,
    )


@router.post("/sync", response_model=DeliverySyncResponse)
def sync_orders(
    lookback_hours: int = Query(24, ge=1, le=720),
    limit: int = Query(500, ge=1, le=500),
    current_user: CurrentUser = Depends(
        require_permission("delivery.orders.sync")
    ),
    db: Session = Depends(get_business_db),
) -> DeliverySyncResponse:
    return DeliveryService(db).sync(
        lookback_hours=lookback_hours,
        limit=limit,
        actor_username=current_user.username,
    )


@router.get("/riders", response_model=list[DeliveryRiderResponse])
def get_riders(
    _user: CurrentUser = Depends(require_permission("delivery.orders.view")),
    db: Session = Depends(get_business_db),
) -> list[DeliveryRiderResponse]:
    return DeliveryService(db).list_riders()


@router.post(
    "/riders",
    response_model=DeliveryRiderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rider(
    body: DeliveryRiderCreate,
    _user: CurrentUser = Depends(require_permission("delivery.riders.manage")),
    db: Session = Depends(get_business_db),
) -> DeliveryRiderResponse:
    return DeliveryService(db).create_rider(body)


@router.put("/riders/{rider_id}", response_model=DeliveryRiderResponse)
def update_rider(
    rider_id: int,
    body: DeliveryRiderUpdate,
    _user: CurrentUser = Depends(require_permission("delivery.riders.manage")),
    db: Session = Depends(get_business_db),
) -> DeliveryRiderResponse:
    return DeliveryService(db).update_rider(rider_id, body)


@router.delete("/riders/{rider_id}", response_model=DeliveryRiderResponse)
def deactivate_rider(
    rider_id: int,
    _user: CurrentUser = Depends(require_permission("delivery.riders.manage")),
    db: Session = Depends(get_business_db),
) -> DeliveryRiderResponse:
    return DeliveryService(db).set_rider_active(rider_id, is_active=False)


@router.post(
    "/orders/bulk-assign",
    response_model=DeliveryBulkActionResponse,
)
def bulk_assign_orders(
    body: DeliveryAssignRequest,
    current_user: CurrentUser = Depends(
        require_permission("delivery.orders.assign")
    ),
    db: Session = Depends(get_business_db),
) -> DeliveryBulkActionResponse:
    return DeliveryService(db).bulk_assign_orders(
        body,
        actor_username=current_user.username,
    )


@router.post(
    "/orders/bulk-deliver",
    response_model=DeliveryBulkActionResponse,
)
def bulk_deliver_assigned_orders(
    body: DeliveryBulkDeliverRequest,
    current_user: CurrentUser = Depends(
        require_permission("delivery.orders.update")
    ),
    db: Session = Depends(get_business_db),
) -> DeliveryBulkActionResponse:
    return DeliveryService(db).bulk_deliver_assigned_orders(
        body,
        actor_username=current_user.username,
    )


@router.put("/orders/{order_id}/assign", response_model=DeliveryOrderResponse)
def assign_order(
    order_id: int,
    body: DeliveryAssignRequest,
    current_user: CurrentUser = Depends(
        require_permission("delivery.orders.assign")
    ),
    db: Session = Depends(get_business_db),
) -> DeliveryOrderResponse:
    return DeliveryService(db).assign_order(
        order_id,
        body,
        actor_username=current_user.username,
    )


@router.put("/orders/{order_id}/status", response_model=DeliveryOrderResponse)
def update_order_status(
    order_id: int,
    body: DeliveryStatusUpdateRequest,
    current_user: CurrentUser = Depends(
        require_permission("delivery.orders.update")
    ),
    db: Session = Depends(get_business_db),
) -> DeliveryOrderResponse:
    return DeliveryService(db).update_status(
        order_id,
        body,
        actor_username=current_user.username,
    )
