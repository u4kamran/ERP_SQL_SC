"""FIN_ITEM data access repository."""

from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.business.fin_item import FinItem


class FinItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, item_id: float) -> Optional[FinItem]:
        return self.db.get(FinItem, item_id)

    def list_items(
        self, skip: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> Tuple[List[FinItem], int]:
        stmt = select(FinItem)
        count_stmt = select(func.count()).select_from(FinItem)

        if search:
            pattern = f"%{search}%"
            filt = or_(
                FinItem.ITEM_TITLE.like(pattern),
                FinItem.ITEM_SHORT.like(pattern),
                FinItem.barcodeid.like(pattern),
            )
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)

        total = self.db.execute(count_stmt).scalar() or 0
        stmt = stmt.order_by(FinItem.manualid.desc()).offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def next_ids(self) -> Tuple[float, int]:
        max_item_id = self.db.execute(select(func.max(FinItem.ITEM_ID))).scalar() or 0
        max_manualid = self.db.execute(select(func.max(FinItem.manualid))).scalar() or 0
        return float(max_item_id) + 1, int(max_manualid) + 1

    def create(self, item: FinItem) -> FinItem:
        self.db.add(item)
        self.db.flush()
        return item

    def update(self, item: FinItem) -> FinItem:
        self.db.flush()
        return item

    def delete(self, item: FinItem):
        self.db.delete(item)
        self.db.flush()
