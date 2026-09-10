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
    PublicCategory,
    PublicCategoryPage,
    PublicProduct,
)
from app.repositories.item_search_support_repository import ItemSearchSupportRepository
from app.services.fin_item_classic_service import FinItemClassicService, _safe_float, _vget
from app.services.guest_price_lookup_service import is_hidden_shop_title, to_proper_case
from app.services.item_images.service import ItemImagesService


class PublicCatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.classic = FinItemClassicService(db)
        self._image_svc = ItemImagesService(db)

    def _image_url_for_manual(self, manual_id: int) -> str | None:
        try:
            return self._image_svc.resolve_public_url_for_manual_id(int(manual_id))
        except Exception:
            return None

    def _from_detail(self, detail) -> PublicProduct:
        stock = _safe_float(getattr(detail, "cqty", None))
        manual_id = int(detail.manual_id or 0)
        return PublicProduct(
            manual_id=manual_id,
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
            image_url=self._image_url_for_manual(manual_id) if manual_id else None,
        )

    def _from_row(self, row) -> PublicProduct | None:
        manual_id = int(_vget(row, "manualid", "manual_id") or 0)
        if manual_id <= 0:
            return None
        title = to_proper_case(_vget(row, "ITEM_TITLE", "item_title")) or ""
        if is_hidden_shop_title(title) or is_hidden_shop_title(
            _vget(row, "ITEM_TITLE", "item_title")
        ):
            return None
        sales = _safe_float(_vget(row, "SALES_RATE", "sales_rate"))
        gst = _safe_float(_vget(row, "OAMT1", "oamt1")) or 0.0
        stock = _safe_float(_vget(row, "CQTY", "cqty"))
        return PublicProduct(
            manual_id=manual_id,
            barcodeid=_vget(row, "barcodeid"),
            barcodeid_ws=_vget(row, "BARCODEID_WS", "barcodeid_ws"),
            item_title=title,
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
            image_url=self._image_url_for_manual(manual_id),
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
        product = self._from_detail(detail)
        if is_hidden_shop_title(product.item_title) or is_hidden_shop_title(
            getattr(detail, "item_title", None)
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )
        return product

    def _category_range(self, category_id: int) -> tuple[float, float] | None:
        row = self.db.execute(
            text("SELECT item_id, Ac_Level FROM fin_cat WHERE item_id = :cid"),
            {"cid": float(category_id)},
        ).mappings().first()
        if not row:
            return None
        level = int(row.get("Ac_Level") or row.get("AC_LEVEL") or 0)
        start = float(row.get("item_id") or 0)
        if start <= 0:
            return None
        span = 10_000_000.0 if level <= 1 else 10_000.0
        return start, start + span

    def _search_tokens(self, q: str) -> list[str]:
        raw = (q or "").strip()
        if not raw:
            return []
        try:
            alias = ItemSearchSupportRepository(self.db).lookup_alias(raw)
            if alias:
                raw = f"{raw} {alias}"
        except Exception:
            self.db.rollback()
        parts = [p for p in raw.replace(",", " ").split() if p]
        tokens: list[str] = []
        for part in parts[:4]:
            cleaned = part[:40]
            if cleaned and cleaned.lower() not in {"a", "an", "the", "of"}:
                tokens.append(cleaned)
        return tokens or [raw[:40]]

    def list_categories(self, parent_id: int | None = None) -> PublicCategoryPage:
        if parent_id:
            rng = self._category_range(parent_id)
            if not rng:
                return PublicCategoryPage(items=[])
            start, end = rng
            sql = """
                SELECT item_id, Item_Title, Ac_Level
                FROM fin_cat
                WHERE Ac_Level = 2
                  AND item_id >= :start AND item_id < :end
                  AND item_id <> :parent_id
                ORDER BY Item_Title
            """
            params = {"start": start, "end": end, "parent_id": float(parent_id)}
        else:
            sql = """
                SELECT item_id, Item_Title, Ac_Level
                FROM fin_cat
                WHERE Ac_Level = 1
                ORDER BY Item_Title
            """
            params = {}
        rows = list(self.db.execute(text(sql), params).mappings().all())
        items: list[PublicCategory] = []
        for row in rows:
            title = to_proper_case(_vget(row, "Item_Title", "ITEM_TITLE")) or ""
            raw = str(title).strip()
            if not raw or raw.replace(".", "").isdigit():
                continue
            if raw.lower() == "test":
                continue
            if is_hidden_shop_title(raw):
                continue
            cat_id = int(float(_vget(row, "item_id") or 0))
            if cat_id <= 0:
                continue
            items.append(
                PublicCategory(
                    category_id=cat_id,
                    title=raw,
                    level=int(_vget(row, "Ac_Level", "AC_LEVEL") or 0),
                )
            )
        return PublicCategoryPage(items=items)

    def list_products(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        promo_only: bool = False,
        q: str | None = None,
        category_id: int | None = None,
    ) -> PublicCatalogPage:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 40)
        offset = (page - 1) * page_size

        where = [
            "ISNULL(FIN_ITEM.manualid, 0) > 0",
            "ISNULL(FIN_ITEM.SALES_RATE, 0) > 0",
            "LOWER(LEFT(LTRIM(ISNULL(FIN_ITEM.ITEM_TITLE, '')), 5)) <> N'empty'",
        ]
        params: dict = {"take": page_size + 1, "skip": offset}

        if promo_only:
            where.append("ISNULL(FIN_ITEM.CRITICAL_LEVEL1, 0) > 0")

        if q and q.strip():
            tokens = self._search_tokens(q)
            for i, tok in enumerate(tokens):
                params[f"tok{i}"] = f"%{tok}%"
                params[f"pre{i}"] = f"{tok}%"
                where.append(
                    "("
                    f"FIN_ITEM.ITEM_TITLE LIKE :pre{i} OR FIN_ITEM.ITEM_TITLE LIKE :tok{i} "
                    f"OR FIN_ITEM.ITEM_SHORT LIKE :pre{i} OR FIN_ITEM.ITEM_SHORT LIKE :tok{i} "
                    f"OR CAST(FIN_ITEM.manualid AS VARCHAR(32)) LIKE :tok{i} "
                    f"OR ISNULL(FIN_ITEM.barcodeid,'') LIKE :pre{i} OR ISNULL(FIN_ITEM.barcodeid,'') LIKE :tok{i} "
                    f"OR ISNULL(FIN_ITEM.BARCODEID_WS,'') LIKE :pre{i} OR ISNULL(FIN_ITEM.BARCODEID_WS,'') LIKE :tok{i} "
                    f"OR ISNULL(co.co_title,'') LIKE :tok{i}"
                    ")"
                )
            from_sql = "FROM FIN_ITEM LEFT JOIN Co co ON co.Co_id = FIN_ITEM.co_id"
        else:
            from_sql = "FROM FIN_ITEM"

        if category_id:
            rng = self._category_range(category_id)
            if not rng:
                return PublicCatalogPage(items=[], page=page, page_size=page_size, has_more=False)
            params["cat_start"] = rng[0]
            params["cat_end"] = rng[1]
            where.append("FIN_ITEM.ITEM_ID >= :cat_start AND FIN_ITEM.ITEM_ID < :cat_end")

        clause = " AND ".join(where)
        sql = f"""
            SELECT FIN_ITEM.ITEM_ID, FIN_ITEM.ITEM_TITLE, FIN_ITEM.ITEM_SHORT, FIN_ITEM.manualid,
                   FIN_ITEM.barcodeid, FIN_ITEM.BARCODEID_WS, FIN_ITEM.SALES_RATE, FIN_ITEM.OAMT1,
                   FIN_ITEM.DISC_P1, FIN_ITEM.CQTY, FIN_ITEM.CRITICAL_LEVEL1, FIN_ITEM.UOM_ID,
                   FIN_ITEM.co_id
            {from_sql}
            WHERE {clause}
            ORDER BY FIN_ITEM.ITEM_TITLE
            OFFSET :skip ROWS FETCH NEXT :take ROWS ONLY
        """
        try:
            rows = list(self.db.execute(text(sql), params).mappings().all())
        except Exception:
            self.db.rollback()
            sql_top = f"""
                SELECT TOP 200 FIN_ITEM.ITEM_ID, FIN_ITEM.ITEM_TITLE, FIN_ITEM.ITEM_SHORT,
                       FIN_ITEM.manualid, FIN_ITEM.barcodeid, FIN_ITEM.BARCODEID_WS,
                       FIN_ITEM.SALES_RATE, FIN_ITEM.OAMT1, FIN_ITEM.DISC_P1, FIN_ITEM.CQTY,
                       FIN_ITEM.CRITICAL_LEVEL1, FIN_ITEM.UOM_ID, FIN_ITEM.co_id
                {from_sql}
                WHERE {clause}
                ORDER BY FIN_ITEM.ITEM_TITLE
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
