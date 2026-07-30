"""VB6 Fin_Item.frm business logic."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business.fin_item import FinItem
from app.repositories.fin_item_classic_repository import FinItemClassicRepository
from app.schemas.fin_item_classic import (
    FinItemClassicDefaults,
    FinItemClassicDetail,
    FinItemClassicHistory,
    FinItemClassicLookup,
    FinItemClassicSave,
    FinItemClassicSaveResponse,
    FinItemClassicStats,
    FinItemClassicTransactionRow,
)


def _safe_float(value, default=0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _vget(data: Optional[dict], *keys, default=None):
    """Read row values regardless of SQL column casing."""
    if not data:
        return default
    lowered = {str(k).lower(): v for k, v in data.items()}
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
        val = lowered.get(str(key).lower())
        if val is not None:
            return val
    return default


def _nil(value: Optional[str]) -> str:
    text = (value or "").strip()
    return text if text else "Nil"


class FinItemClassicService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FinItemClassicRepository(db)

    def get_stats(self) -> FinItemClassicStats:
        count, last_id = self.repo.get_stats()
        return FinItemClassicStats(record_count=count, last_item_id=last_id)

    def get_defaults(self) -> FinItemClassicDefaults:
        manual_id = self.repo.next_manual_id()
        defaults = FinItemClassicDefaults(manual_id=manual_id)
        defaults.uom_title = self.repo.lookup_uom(defaults.uom_id)
        defaults.country_title = self.repo.lookup_country(defaults.country_id)
        defaults.co_title = self.repo.lookup_company(defaults.co_id)
        return defaults

    def search_items(self, q: str) -> list[FinItemClassicLookup]:
        rows = self.repo.search_items(q)
        results = []
        for row in rows:
            item_id = _vget(row, "item_id", "ITEM_ID")
            manual_id = _vget(row, "manualid", "manual_id")
            title = _vget(row, "Item_Title", "item_title", "ITEM_TITLE") or ""
            short = _vget(row, "item_short", "ITEM_SHORT") or ""
            barcode = _vget(row, "barcodeid", "BARCODEID") or ""
            results.append(
                FinItemClassicLookup(
                    id=item_id,
                    title=title,
                    manual_id=int(manual_id) if manual_id is not None else None,
                    item_short=short,
                    barcodeid=str(barcode) if barcode else None,
                )
            )
        return results

    def load_item_id(self, item_id: float, history_limit: int = 0) -> FinItemClassicDetail:
        cat = self.repo.get_fin_cat(item_id)
        if not cat:
            manual_item = self.repo.get_by_manual_id(int(item_id))
            if manual_item:
                real_id = _vget(manual_item, "ITEM_ID", "item_id")
                return self.load_item_id(float(real_id), history_limit)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item ID not found in Finished Category (FIN_CAT).",
            )
        if int(_vget(cat, "Ac_Level", "AC_LEVEL") or 0) != 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid: Use Item ID at level 4.",
            )

        item_row = self.repo.get_item_dict(item_id)
        return self._build_detail(cat, item_row, history_limit)

    def load_manual_id(self, manual_id: int, history_limit: int = 0) -> FinItemClassicDetail:
        item_row = self.repo.get_by_manual_id(manual_id)
        if not item_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual ID not found.")
        item_id = float(_vget(item_row, "ITEM_ID", "item_id"))
        cat = self.repo.get_fin_cat(item_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item category not found for this manual ID.",
            )
        return self._build_detail(cat, item_row, history_limit)

    def load_barcode(self, barcode: str, history_limit: int = 0) -> FinItemClassicDetail:
        if not barcode or barcode == "0":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid barcode.")
        item_row = self.repo.get_by_barcode(barcode)
        if not item_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found.")
        item_id = float(_vget(item_row, "ITEM_ID", "item_id"))
        cat = self.repo.get_fin_cat(item_id) or {
            "item_id": item_id,
            "Item_Title": _vget(item_row, "ITEM_TITLE"),
            "Ac_Level": 4,
        }
        return self._build_detail(cat, item_row, history_limit)

    def load_ws_barcode(self, barcode: str, history_limit: int = 0) -> FinItemClassicDetail:
        if not barcode or barcode == "0":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid WS barcode.")
        item_row = self.repo.get_by_ws_barcode(barcode)
        if not item_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="WS Barcode not found.")
        item_id = float(_vget(item_row, "ITEM_ID", "item_id"))
        cat = self.repo.get_fin_cat(item_id) or {
            "item_id": item_id,
            "Item_Title": _vget(item_row, "ITEM_TITLE"),
            "Ac_Level": 4,
        }
        return self._build_detail(cat, item_row, history_limit)

    def get_history(self, item_id: float, limit: int = 5) -> FinItemClassicHistory:
        return FinItemClassicHistory(
            last_purchases=self._map_purchases(item_id, limit),
            last_sales=self._map_sales(item_id, limit),
        )

    def save(self, data: FinItemClassicSave) -> FinItemClassicSaveResponse:
        self._validate_save(data)

        cat = self.repo.get_fin_cat(data.item_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item ID not found in Finished Category (FIN_CAT).",
            )

        existing = self.repo.get_fin_item_row(data.item_id)
        is_new = existing is None

        if is_new:
            item = FinItem(ITEM_ID=data.item_id, manualid=data.manual_id)
        else:
            item = existing

        sales_rate = _safe_float(data.sales_rate)
        item.ITEM_TITLE = data.item_title or cat.get("Item_Title")
        item.ITEM_SHORT = _nil(data.item_short)
        item.AC_LEVEL = 4
        item.ED_STATUS = 1 if data.ed_status else 0
        item.ITEM_OEM = _nil(data.item_oem)
        item.manualid = data.manual_id
        item.barcodeid = str(data.barcodeid or "0")
        item.BARCODEID_WS = str(data.barcodeid_ws or "0")
        item.VISACARD_RATE = _safe_float(data.visacard_rate)
        item.UOM_ID = data.uom_id
        item.COUNTRY_ID = data.country_id
        item.ITEM_NATURE = data.item_nature
        item.MIN_LEVEL = _safe_float(data.min_level)
        item.MAX_LEVEL = _safe_float(data.max_level)
        item.RO_QTY = _safe_float(data.ro_qty)
        item.CRITICAL_LEVEL = _safe_float(data.critical_level)
        item.MIN_LEVEL1 = _safe_float(data.min_level1)
        item.MAX_LEVEL1 = _safe_float(data.max_level1)
        item.RO_QTY1 = _safe_float(data.ro_qty1)
        item.CRITICAL_LEVEL1 = 1.0 if data.promotion else 0.0
        item.OQTY1 = _safe_float(data.sales_price_wo_gst)
        item.SALES_RATE = sales_rate
        item.COST_RATE = _safe_float(data.cost_rate)
        item.DISC_P1 = _safe_float(data.market_price)
        item.DISC_P2 = 0
        item.DISC_P3 = 0
        item.DISC_P4 = _safe_float(data.ws_price)
        item.GL_SALES_ID = data.gl_sales_id
        item.GL_PUR_ID = data.gl_pur_id
        item.GL_CONS_ID = data.gl_cons_id
        item.GL_DISC_ID = data.gl_disc_id
        item.GL_STAX_ID = data.gl_stax_id
        item.STAX_REG = _safe_float(data.stax_reg)
        item.STAX_UNREG = _safe_float(data.stax_unreg)
        item.REMARKS = _nil(data.remarks)
        item.co_id = data.co_id

        if is_new:
            self.repo.save_item(item)
        else:
            self.db.flush()

        self.db.commit()
        return FinItemClassicSaveResponse(
            message="New Item Inserted." if is_new else "Item Updated.",
            is_new=is_new,
            item_id=data.item_id,
        )

    def delete(self, item_id: float) -> None:
        item = self.repo.get_fin_item_row(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

        if _safe_float(item.CQTY) > 0 or _safe_float(item.CAMT) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete: item contains balance quantity/amount.",
            )

        ledger_count = self.repo.ledger_count(item_id)
        if ledger_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete: item contains {ledger_count} transaction(s) in FIN_LDGR.",
            )

        self.repo.delete_item(item_id)
        self.db.commit()

    def lookup(self, kind: str, lookup_id: int) -> FinItemClassicLookup:
        title = None
        if kind == "uom":
            title = self.repo.lookup_uom(lookup_id)
        elif kind == "country":
            title = self.repo.lookup_country(lookup_id)
        elif kind == "company":
            title = self.repo.lookup_company(lookup_id)
        elif kind == "gl":
            title = self.repo.lookup_gl(lookup_id)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid lookup type.")

        if not title:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{kind.upper()} ID not found.")
        return FinItemClassicLookup(id=lookup_id, title=title)

    def _validate_save(self, data: FinItemClassicSave) -> None:
        if _safe_float(data.min_level) > _safe_float(data.max_level) and _safe_float(data.max_level) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid: Min Level greater than Max Level.",
            )

    def _build_detail(
        self, cat: dict, item_row: Optional[dict], history_limit: int
    ) -> FinItemClassicDetail:
        item_id = float(_vget(cat, "item_id", "ITEM_ID"))
        item_title = (
            _vget(item_row, "ITEM_TITLE", "item_title", "Item_Title")
            or _vget(cat, "Item_Title", "item_title", "ITEM_TITLE")
            or ""
        )
        is_existing = item_row is not None

        detail = FinItemClassicDetail(
            item_id=item_id,
            item_title=item_title,
            status_label="Edit" if is_existing else "New",
            is_existing=is_existing,
        )

        if not is_existing:
            detail.item_short = item_title[:10] if item_title else ""
            return detail

        sales_rate = _safe_float(_vget(item_row, "sales_Rate", "SALES_RATE", "sales_rate"))
        gst = _safe_float(_vget(item_row, "oamt1", "OAMT1"))
        cost_wo_gst = _safe_float(_vget(item_row, "camt1", "CAMT1"))
        saved_cost = _safe_float(_vget(item_row, "cost_Rate", "COST_RATE", "cost_rate"))

        if not sales_rate and not saved_cost:
            rates = self.repo.get_item_rates(item_id)
            if rates:
                sales_rate = sales_rate or _safe_float(_vget(rates, "SALES_RATE", "sales_rate"))
                saved_cost = saved_cost or _safe_float(_vget(rates, "COST_RATE", "cost_rate"))
                gst = gst or _safe_float(_vget(rates, "OAMT1", "oamt1"))
                cost_wo_gst = cost_wo_gst or _safe_float(_vget(rates, "CAMT1", "camt1"))

        # VB6: TxtCost_Price = CDbl(txtCostWOGST) + CDbl(txtGST)
        cost_rate = cost_wo_gst + gst
        if cost_rate == 0:
            cost_rate = saved_cost

        uom_id = _vget(item_row, "UOM_ID")
        country_id = _vget(item_row, "COUNTRY_ID")
        co_id = _vget(item_row, "co_id", "CO_ID")
        gl_ids = [
            _vget(item_row, "GL_SALES_ID"),
            _vget(item_row, "GL_PUR_ID"),
            _vget(item_row, "GL_CONS_ID"),
            _vget(item_row, "GL_DISC_ID"),
            _vget(item_row, "GL_STAX_ID"),
        ]
        gl_titles = self.repo.lookup_gl_titles([i for i in gl_ids if i])

        detail.item_short = _vget(item_row, "ITEM_SHORT") or item_title[:10]
        detail.item_oem = _vget(item_row, "ITEM_OEM")
        detail.manual_id = int(_vget(item_row, "manualid", default=0) or 0)
        detail.barcodeid = str(_vget(item_row, "barcodeid", "BARCODEID") or "0")
        detail.barcodeid_ws = str(_vget(item_row, "BARCODEID_WS", "barcodeid_ws") or "0")
        detail.visacard_rate = _safe_float(_vget(item_row, "VISACARD_RATE"))
        detail.uom_id = uom_id
        detail.uom_title = _vget(item_row, "UOM_ABBR", "uom_abbr") or (
            self.repo.lookup_uom(int(uom_id)) if uom_id else None
        )
        detail.country_id = country_id
        detail.country_title = _vget(item_row, "COUNTRY_TITLE", "country_title") or (
            self.repo.lookup_country(int(country_id)) if country_id else None
        )
        detail.item_nature = _vget(item_row, "ITEM_NATURE") or 0
        detail.min_level = _safe_float(_vget(item_row, "Min_Level", "MIN_LEVEL"))
        detail.max_level = _safe_float(_vget(item_row, "Max_Level", "MAX_LEVEL"))
        detail.ro_qty = _safe_float(_vget(item_row, "RO_qty", "RO_QTY"))
        detail.critical_level = _safe_float(_vget(item_row, "critical_level", "CRITICAL_LEVEL"))

        store_row = self.repo.get_fin_item_store_row(item_id)
        if store_row:
            detail.min_level1 = _safe_float(_vget(store_row, "MIN_LEVEL1"))
            detail.max_level1 = _safe_float(_vget(store_row, "MAX_LEVEL1"))
            detail.ro_qty1 = _safe_float(_vget(store_row, "RO_QTY1"))
            detail.promotion = _safe_float(_vget(store_row, "CRITICAL_LEVEL1")) > 0
        else:
            detail.min_level1 = _safe_float(_vget(item_row, "MIN_LEVEL1"))
            detail.max_level1 = _safe_float(_vget(item_row, "MAX_LEVEL1"))
            detail.ro_qty1 = _safe_float(_vget(item_row, "RO_QTY1"))
            detail.promotion = _safe_float(_vget(item_row, "CRITICAL_LEVEL1")) > 0
        detail.sales_rate = sales_rate
        detail.cost_rate = cost_rate
        detail.saved_cost_price = saved_cost
        detail.gst_amount = gst
        detail.cost_wo_gst = cost_wo_gst
        detail.sales_price_wo_gst = sales_rate - gst
        detail.market_price = _safe_float(_vget(item_row, "disc_p1", "DISC_P1"))
        detail.ws_price = _safe_float(_vget(item_row, "disc_p4", "DISC_P4"))
        detail.tp_rate = _safe_float(_vget(item_row, "cqty1", "CQTY1"))
        detail.gl_sales_id = gl_ids[0]
        detail.gl_pur_id = gl_ids[1]
        detail.gl_cons_id = gl_ids[2]
        detail.gl_disc_id = gl_ids[3]
        detail.gl_stax_id = gl_ids[4]
        detail.gl_sales_title = _vget(item_row, "GL_SALES_TITLE", "gl_sales_title") or (
            gl_titles.get(int(gl_ids[0])) if gl_ids[0] else None
        )
        detail.gl_pur_title = _vget(item_row, "GL_PUR_TITLE", "gl_pur_title") or (
            gl_titles.get(int(gl_ids[1])) if gl_ids[1] else None
        )
        detail.gl_cons_title = _vget(item_row, "GL_CONS_TITLE", "gl_cons_title") or (
            gl_titles.get(int(gl_ids[2])) if gl_ids[2] else None
        )
        detail.gl_disc_title = _vget(item_row, "GL_DISC_TITLE", "gl_disc_title") or (
            gl_titles.get(int(gl_ids[3])) if gl_ids[3] else None
        )
        detail.gl_stax_title = _vget(item_row, "GL_STAX_TITLE", "gl_stax_title") or (
            gl_titles.get(int(gl_ids[4])) if gl_ids[4] else None
        )
        detail.stax_reg = _safe_float(_vget(item_row, "STAX_REG"))
        detail.stax_unreg = _safe_float(_vget(item_row, "STAX_UNREG"))
        detail.oqty = _safe_float(_vget(item_row, "OQTY"))
        detail.cqty = _safe_float(_vget(item_row, "CQTY"))
        detail.oamt = _safe_float(_vget(item_row, "OAMT"))
        detail.camt = _safe_float(_vget(item_row, "CAMT"))
        detail.remarks = _vget(item_row, "REMARKS")
        detail.co_id = co_id
        detail.co_title = _vget(item_row, "co_TITLE", "co_title", "CO_TITLE") or (
            self.repo.lookup_company(int(co_id)) if co_id else None
        )
        detail.ed_status = bool(int(_vget(item_row, "ED_STATUS") or 0))

        if detail.cqty and detail.cqty != 0:
            detail.average_cost = _safe_float(detail.camt) / detail.cqty
        # VB6 TxtSalesPWoGST_Validate profit formula
        if detail.sales_price_wo_gst and detail.cost_wo_gst and detail.sales_price_wo_gst > 0:
            detail.profit_percent = (
                (detail.sales_price_wo_gst - detail.cost_wo_gst) / detail.sales_price_wo_gst
            ) * 100

        if history_limit > 0:
            detail.last_purchases = self._map_purchases(item_id, history_limit)
            detail.last_sales = self._map_sales(item_id, history_limit)

        return detail

    def _map_purchases(self, item_id: float, limit: int) -> list[FinItemClassicTransactionRow]:
        return [
            FinItemClassicTransactionRow(
                doc_no=str(_vget(r, "PROD_ID") or ""),
                doc_date=_vget(r, "doc_date"),
                party_title=_vget(r, "supplier_title"),
                qty=_safe_float(_vget(r, "QTY")),
                rate=_safe_float(_vget(r, "rate", "RATE")),
                extra=str(_vget(r, "Exp_Date")) if _vget(r, "Exp_Date") else None,
            )
            for r in self.repo.last_purchases(item_id, limit)
        ]

    def _map_sales(self, item_id: float, limit: int) -> list[FinItemClassicTransactionRow]:
        return [
            FinItemClassicTransactionRow(
                doc_no=str(_vget(r, "INV_ID", "Inv_ID") or ""),
                doc_date=_vget(r, "doc_date", "DOC_DATE"),
                party_title=_vget(r, "customer_title", "CUSTOMER_TITLE"),
                qty=_safe_float(_vget(r, "QTY")),
                rate=_safe_float(_vget(r, "rate", "RATE")),
            )
            for r in self.repo.last_sales(item_id, limit)
        ]
