"""AI Purchase Automation API — upload invoice → process → review → manual save."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import CurrentUser, require_permission
from app.config.settings import settings
from app.database.business_session import get_business_db
from app.database.session import get_db
from app.models.user import UserPreference
from app.schemas.fin_pur import FinPurSaveResponse
from app.schemas.purchase_automation import (
    PurchaseAutoInstructionsRequest,
    PurchaseAutoInstructionsResponse,
    PurchaseAutoJsonImportRequest,
    PurchaseAutoLearnRequest,
    PurchaseAutoLearnResponse,
    PurchaseAutoProcessResponse,
    PurchaseAutoSaveRequest,
)
from app.services.purchase_automation_service import PurchaseAutomationService

router = APIRouter()

ALLOWED_MIME = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}
MAX_BYTES = 15 * 1024 * 1024


def _legacy_uid(db: Session, user_id: int) -> int:
    row = db.execute(
        select(UserPreference).where(
            UserPreference.UserId == user_id,
            UserPreference.PreferenceKey == "legacy_contpl_uid",
            UserPreference.IsDeleted == False,  # noqa: E712
        )
    ).scalar_one_or_none()
    if row and row.PreferenceValue:
        try:
            return int(row.PreferenceValue)
        except ValueError:
            pass
    return settings.voucher_legacy_uid


def _service(current_user: CurrentUser, business_db: Session, auth_db: Session) -> PurchaseAutomationService:
    return PurchaseAutomationService(
        business_db,
        username=current_user.username,
        legacy_uid=_legacy_uid(auth_db, current_user.user_id),
        is_admin=current_user.has_permission("auth.admin.full"),
    )


@router.get("/instructions", response_model=PurchaseAutoInstructionsResponse)
def get_instructions(
    current_user: CurrentUser = Depends(require_permission("inventory.fin_pur.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    """Load saved fetch instructions for Purchase Automation."""
    return _service(current_user, business_db, auth_db).get_instructions()


@router.put("/instructions", response_model=PurchaseAutoInstructionsResponse)
def save_instructions(
    payload: PurchaseAutoInstructionsRequest,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_pur.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    """Persist fetch instructions for future Process runs."""
    return _service(current_user, business_db, auth_db).save_instructions(payload.instructions)


@router.post("/process", response_model=PurchaseAutoProcessResponse)
async def process_invoice(
    file: UploadFile = File(...),
    instructions: str = Form(""),
    current_user: CurrentUser = Depends(require_permission("inventory.fin_pur.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    mime_type = (file.content_type or "").lower().strip()
    filename = (file.filename or "").lower()
    if mime_type not in ALLOWED_MIME:
        if filename.endswith(".pdf"):
            mime_type = "application/pdf"
        elif filename.endswith((".jpg", ".jpeg")):
            mime_type = "image/jpeg"
        elif filename.endswith(".png"):
            mime_type = "image/png"
        elif filename.endswith(".webp"):
            mime_type = "image/webp"
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Upload a PDF, JPG, PNG, or WebP supplier invoice.",
            )

    file_bytes = await file.read(MAX_BYTES + 1)
    await file.close()
    if len(file_bytes) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must not exceed 15 MB.",
        )
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    svc = _service(current_user, business_db, auth_db)
    return await run_in_threadpool(
        svc.process,
        file_bytes=file_bytes,
        mime_type=mime_type,
        instructions=instructions or "",
    )


@router.post("/import-json", response_model=PurchaseAutoProcessResponse)
def import_json(
    payload: PurchaseAutoJsonImportRequest,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_pur.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    """Fill the review grid from pasted invoice JSON — items resolved by manual ID first."""
    return _service(current_user, business_db, auth_db).import_json(
        json_text=payload.json_text, data=payload.data
    )


@router.post("/save", response_model=FinPurSaveResponse)
def save_purchase(
    payload: PurchaseAutoSaveRequest,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_pur.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    """Manual Save Purchase — same Fin_Pur_M / Fin_Pur_D / GL path as Purchase Receipt."""
    return _service(current_user, business_db, auth_db).save(payload)


@router.post("/learn", response_model=PurchaseAutoLearnResponse)
def learn_corrections(
    payload: PurchaseAutoLearnRequest,
    current_user: CurrentUser = Depends(require_permission("inventory.fin_pur.create")),
    business_db: Session = Depends(get_business_db),
    auth_db: Session = Depends(get_db),
):
    """Stage 13 — persist supplier aliases / handwritten ID mappings from user corrections."""
    return _service(current_user, business_db, auth_db).learn(payload)
