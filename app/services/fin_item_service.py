"""FIN_ITEM business logic service."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business.fin_item import FinItem
from app.repositories.fin_item_repository import FinItemRepository
from app.schemas.fin_item import FinItemCreate, FinItemListResponse, FinItemResponse, FinItemUpdate


def _apply_base_fields(item: FinItem, data) -> None:
    mapping = {
        "ITEM_TITLE": "item_title",
        "ITEM_SHORT": "item_short",
        "AC_LEVEL": "ac_level",
        "ED_STATUS": "ed_status",
        "ITEM_OEM": "item_oem",
        "barcodeid": "barcodeid",
        "UOM_ID": "uom_id",
        "COUNTRY_ID": "country_id",
        "ITEM_NATURE": "item_nature",
        "MIN_LEVEL": "min_level",
        "MAX_LEVEL": "max_level",
        "RO_QTY": "ro_qty",
        "CRITICAL_LEVEL": "critical_level",
        "VISACARD_RATE": "visacard_rate",
        "SALES_RATE": "sales_rate",
        "COST_RATE": "cost_rate",
        "DISC_P1": "disc_p1",
        "DISC_P2": "disc_p2",
        "DISC_P3": "disc_p3",
        "DISC_P4": "disc_p4",
        "GL_SALES_ID": "gl_sales_id",
        "GL_PUR_ID": "gl_pur_id",
        "GL_CONS_ID": "gl_cons_id",
        "GL_DISC_ID": "gl_disc_id",
        "GL_STAX_ID": "gl_stax_id",
        "STAX_REG": "stax_reg",
        "STAX_UNREG": "stax_unreg",
        "REMARKS": "remarks",
        "co_id": "co_id",
        "MIN_LEVEL1": "min_level1",
        "MAX_LEVEL1": "max_level1",
        "RO_QTY1": "ro_qty1",
        "CRITICAL_LEVEL1": "critical_level1",
        "BARCODEID_WS": "barcodeid_ws",
    }
    payload = data.model_dump(exclude_unset=True)
    for col, field in mapping.items():
        if field in payload:
            setattr(item, col, payload[field])


class FinItemService:
    def __init__(self, db: Session):
        self.repo = FinItemRepository(db)
        self.db = db

    def list_items(self, skip: int, limit: int, search: Optional[str]) -> FinItemListResponse:
        items, total = self.repo.list_items(skip, limit, search)
        return FinItemListResponse(
            items=[FinItemResponse.model_validate(i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_item(self, item_id: float) -> FinItemResponse:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
        return FinItemResponse.model_validate(item)

    def create_item(self, data: FinItemCreate) -> FinItemResponse:
        next_item_id, next_manualid = self.repo.next_ids()
        item = FinItem(ITEM_ID=next_item_id, manualid=next_manualid)
        _apply_base_fields(item, data)
        self.repo.create(item)
        self.db.commit()
        self.db.refresh(item)
        return FinItemResponse.model_validate(item)

    def update_item(self, item_id: float, data: FinItemUpdate) -> FinItemResponse:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
        _apply_base_fields(item, data)
        self.repo.update(item)
        self.db.commit()
        self.db.refresh(item)
        return FinItemResponse.model_validate(item)

    def delete_item(self, item_id: float):
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
        self.repo.delete(item)
        self.db.commit()
