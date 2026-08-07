"""Guest/public item price lookup — read-only, no authentication."""

import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.guest_price_lookup import GuestPriceLookupResponse
from app.services.fin_item_classic_service import FinItemClassicService

_UNIT_FIXES = (
    ("Ml", "ML"),
    ("Kg", "KG"),
    ("Gm", "GM"),
    ("Gms", "GMS"),
    ("Pcs", "PCS"),
    ("Pc", "PC"),
    ("Ltr", "LTR"),
    ("Oz", "OZ"),
    ("Pk", "PK"),
    ("Pkt", "PKT"),
)


def to_proper_case(value: str | None) -> str | None:
    """Display titles in Proper Case (e.g. DALDA OIL → Dalda Oil)."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return text
    titled = text.title()
    for wrong, right in _UNIT_FIXES:
        # Allow units next to numbers (1Kg → 1KG), not only whole words.
        titled = re.sub(
            rf"(?<![A-Za-z]){re.escape(wrong)}(?![A-Za-z])",
            right,
            titled,
        )
    return titled


class GuestPriceLookupService:
    def __init__(self, db: Session):
        self.classic = FinItemClassicService(db)

    def lookup_barcode(self, barcode: str) -> GuestPriceLookupResponse:
        detail = self.classic.load_barcode(barcode, history_limit=0)
        return self._to_public(detail)

    def lookup_ws_barcode(self, barcode: str) -> GuestPriceLookupResponse:
        detail = self.classic.load_ws_barcode(barcode, history_limit=0)
        return self._to_public(detail)

    def lookup_any(self, barcode: str) -> GuestPriceLookupResponse:
        """Try retail barcode first, then wholesale barcode."""
        barcode = (barcode or "").strip()
        if not barcode or barcode == "0":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid barcode.")
        try:
            return self.lookup_barcode(barcode)
        except HTTPException as exc:
            if exc.status_code != status.HTTP_404_NOT_FOUND:
                raise
        return self.lookup_ws_barcode(barcode)

    def lookup_manual_id(self, manual_id: int) -> GuestPriceLookupResponse:
        if manual_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid manual ID.")
        from app.services.fin_item_classic_service import _vget

        item_row = self.classic.repo.get_by_manual_id(manual_id)
        if not item_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual ID not found.")
        item_id = float(_vget(item_row, "ITEM_ID", "item_id"))
        cat = self.classic.repo.get_fin_cat(item_id) or {
            "item_id": item_id,
            "Item_Title": _vget(item_row, "ITEM_TITLE"),
            "Ac_Level": 4,
        }
        detail = self.classic._build_detail(cat, item_row, 0)
        return self._to_public(detail)

    @staticmethod
    def _to_public(detail) -> GuestPriceLookupResponse:
        return GuestPriceLookupResponse(
            manual_id=detail.manual_id,
            barcodeid=detail.barcodeid,
            barcodeid_ws=detail.barcodeid_ws,
            item_title=to_proper_case(detail.item_title) or "",
            item_short=to_proper_case(detail.item_short),
            uom_title=to_proper_case(detail.uom_title),
            co_title=to_proper_case(detail.co_title),
            sales_rate=detail.sales_rate,
            sales_price_wo_gst=detail.sales_price_wo_gst,
            gst_amount=detail.gst_amount,
            market_price=detail.market_price,
            promotion=detail.promotion,
        )
