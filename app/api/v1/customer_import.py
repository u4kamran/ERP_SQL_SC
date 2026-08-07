"""Finalize reviewed OCR records into CUST_SMS."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import CurrentUser, require_permission
from app.database.business_session import get_business_db
from app.schemas.customer_import import (
    CustomerImportFinalizeRequest,
    CustomerImportFinalizeResponse,
    CustomerImportExtractResponse,
)
from app.services.customer_import_service import CustomerImportService
from app.services.customer_import_vision_service import CustomerImportVisionService


router = APIRouter()


@router.post("/extract", response_model=CustomerImportExtractResponse)
async def extract_customer_file(
    file: UploadFile = File(...),
    _user: CurrentUser = Depends(
        require_permission("marketing.cust_sms.create")
    ),
) -> CustomerImportExtractResponse:
    mime_type = (file.content_type or "").lower()
    if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a JPG, PNG, or WebP image.",
        )
    image_bytes = await file.read(10 * 1024 * 1024 + 1)
    await file.close()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image size must not exceed 10 MB.",
        )
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is empty.",
        )
    return await run_in_threadpool(
        CustomerImportVisionService().extract,
        image_bytes=image_bytes,
        mime_type=mime_type,
    )


@router.post("/finalize", response_model=CustomerImportFinalizeResponse)
def finalize_customer_import(
    body: CustomerImportFinalizeRequest,
    _user: CurrentUser = Depends(
        require_permission("marketing.cust_sms.create")
    ),
    db: Session = Depends(get_business_db),
) -> CustomerImportFinalizeResponse:
    return CustomerImportService(db).finalize(body)
