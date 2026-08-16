"""Customer-facing catalog browse + cart validation (public, no cost/GL)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.public_catalog import (
    CartValidateLineOut,
    CartValidateRequest,
    CartValidateResponse,
    PublicCatalogPage,
    PublicProduct,
)
from app.services.fin_item_classic_service import FinItemClassicService, _safe_float, _vget
from app.services.guest_price_lookup_service import to_proper_case


class PublicCatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.classic = FinItemClassicService(db)

    def _from_detail(self, detail) -> PublicProduct:
        stock = _safe_float(getattr(detail, "cqty", None))
        return PublicProduct(
            manual_id=int(detail.manual_id or 0),
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
            promotion=bool(detail.promotion),
            stock_qty=stock,
            in_stock=stock is None or stock > 0,
            image_url=None,
        )

    def _from_row(self, row) -> PublicProduct | None:
        manual_id = int(_vget(row, "manualid", "manual_id") or 0)
        if manual_id <= 0:
            return None
        sales = _safe_float(_vget(row, "SALES_RATE", "sales_rate"))
        gst = _safe_float(_vget(row, "OAMT1", "oamt1")) or 0.0
        stock = _safe_float(_vget(row, "CQTY", "cqty"))
        return PublicProduct(
            manual_id=manual_id,
            barcodeid=_vget(row, "barcodeid"),
            barcodeid_ws=_vget(row, "BARCODEID_WS", "barcodeid_ws"),
            item_title=to_proper_case(_vget(row, "ITEM_TITLE", "item_title")) or "",
            item_short=to_proper_case(_vget(row, "ITEM_SHORT", "item_short")),
            uom_title=to_proper_case(_vget(row, "UOM_TITLE", "uom_title", "UOM_ABBR")),
            co_title=to_proper_case(_vget(row, "co_TITLE", "CO_TITLE", "co_title")),
            sales_rate=sales,
            sales_price_wo_gst=(sales - gst) if sales is not None else None,
            gst_amount=gst,
            market_price=_safe_float(_vget(row, "DISC_P1", "disc_p1")),
            promotion=_safe_float(_vget(row, "CRITICAL_LEVEL1", "critical_level1")) > 0,
            stock_qty=stock,
            in_stock=stock is None or stock > 0,
            image_url=None,
        )

    def lookup_manual_id(self, manual_id: int) -> PublicProduct:
        if manual_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product.")
        item_row = self.classic.repo.get_by_manual_id(manual_id)
        if not item_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        item_id = float(_vget(item_row, "ITEM_ID", "item_id"))
        cat = self.classic.repo.get_fin_cat(item_id) or {
            "item_id": item_id,
            "Item_Title": _vget(item_row, "ITEM_TITLE"),
            "Ac_Level": 4,
        }
        detail = self.classic._build_detail(cat, item_row, 0)
        return self._from_detail(detail)

    def list_products(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        promo_only: bool = False,
        q: str | None = None,
    ) -> PublicCatalogPage:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 40)
        offset = (page - 1) * page_size

        where = ["ISNULL(manualid, 0) > 0", "ISNULL(SALES_RATE, 0) > 0"]
        params: dict = {"take": page_size + 1, "skip": offset}

        if promo_only:
            where.append("ISNULL(CRITICAL_LEVEL1, 0) > 0")

        if q and q.strip():
            where.append(
                "(ITEM_TITLE LIKE :q OR ITEM_SHORT LIKE :q OR CAST(manualid AS VARCHAR(32)) LIKE :q "
                "OR ISNULL(barcodeid,'') LIKE :q OR ISNULL(BARCODEID_WS,'') LIKE :q)"
            )
            params["q"] = f"%{q.strip()}%"

        clause = " AND ".join(where)
        sql = f"""
            SELECT ITEM_ID, ITEM_TITLE, ITEM_SHORT, manualid, barcodeid, BARCODEID_WS,
                   SALES_RATE, OAMT1, DISC_P1, CQTY, CRITICAL_LEVEL1, UOM_ID, co_id
            FROM FIN_ITEM
            WHERE {clause}
            ORDER BY ITEM_TITLE
            OFFSET :skip ROWS FETCH NEXT :take ROWS ONLY
        """
        try:
            rows = list(self.db.execute(text(sql), params).mappings().all())
        except Exception:
            self.db.rollback()
            # Fallback without OFFSET (older engines)
            sql_top = f"""
                SELECT TOP 200 ITEM_ID, ITEM_TITLE, ITEM_SHORT, manualid, barcodeid, BARCODEID_WS,
                       SALES_RATE, OAMT1, DISC_P1, CQTY, CRITICAL_LEVEL1, UOM_ID, co_id
                FROM FIN_ITEM
                WHERE {clause}
                ORDER BY ITEM_TITLE
            """
            all_rows = list(self.db.execute(text(sql_top), params).mappings().all())
            rows = all_rows[offset : offset + page_size + 1]

        has_more = len(rows) > page_size
        items = []
        for row in rows[:page_size]:
            product = self._from_row(row)
            if product:
                items.append(product)

        return PublicCatalogPage(
            items=items,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    def validate_cart(self, payload: CartValidateRequest) -> CartValidateResponse:
        out_lines: list[CartValidateLineOut] = []
        changed = False
        subtotal = 0.0

        for line in payload.lines:
            try:
                product = self.lookup_manual_id(line.manual_id)
            except HTTPException:
                changed = True
                out_lines.append(
                    CartValidateLineOut(
                        manual_id=line.manual_id,
                        qty=line.qty,
                        ok=False,
                        message="This product is no longer available.",
                    )
                )
                continue

            qty = float(line.qty)
            stock = product.stock_qty
            msg = None
            ok = True
            if stock is not None and stock <= 0:
                ok = False
                changed = True
                msg = "This product is currently out of stock."
            elif stock is not None and qty > stock:
                ok = False
                changed = True
                qty = max(float(stock), 0.0)
                display = int(stock) if float(stock).is_integer() else stock
                msg = f"Only {display} units are currently available."

            unit = float(product.sales_rate or 0)
            line_total = round(unit * qty, 2)
            if ok and unit > 0:
                subtotal += line_total

            out_lines.append(
                CartValidateLineOut(
                    manual_id=product.manual_id,
                    qty=qty,
                    item_title=product.item_title,
                    item_short=product.item_short,
                    barcodeid=product.barcodeid,
                    uom_title=product.uom_title,
                    co_title=product.co_title,
                    unit_price=unit,
                    sales_price_wo_gst=product.sales_price_wo_gst,
                    gst_amount=product.gst_amount,
                    market_price=product.market_price,
                    promotion=product.promotion,
                    stock_qty=product.stock_qty,
                    in_stock=product.in_stock,
                    line_total=line_total,
                    ok=ok,
                    message=msg,
                    image_url=product.image_url,
                )
            )

        return CartValidateResponse(
            lines=out_lines,
            subtotal=round(subtotal, 2),
            estimated_total=round(subtotal, 2),
            changed=changed,
            message=(
                "The price or availability of one or more items has changed. Please review your cart."
                if changed
                else None
            ),
        )
