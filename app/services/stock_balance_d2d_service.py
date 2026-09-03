"""Stock Balance Date to Date — VB6 RptStD2D / RptStD2DAmtBrand / FrmPrintInvL."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.stock_balance_d2d_repository import MAX_ITEM_ID, StockBalanceD2DRepository
from app.schemas.stock_balance_d2d import (
    StockBalanceD2DData,
    StockBalanceD2DRequest,
    StockBalanceD2DRow,
    StockBalanceD2DTotals,
    StockItemLookup,
)
from app.utils.gl_format import dash_item


def _passes_zero_filter(
    *,
    qty_opening: float,
    qty_in: float,
    qty_out: float,
    qty_closing: float,
    suppress_zero: bool,
) -> bool:
    """VB6 Option_Check1 always filters on qty fields (even when Print Amount)."""
    if not suppress_zero:
        return True
    return (
        abs(qty_opening) + abs(qty_in) + abs(qty_out) + abs(qty_closing)
    ) > 0


def _brand_label(manualid: int, show_manual_id: bool) -> str:
    if not show_manual_id:
        return "Nil"
    if not manualid:
        return "Nil"
    return str(int(manualid))


class StockBalanceD2DService:
    def __init__(self, db: Session):
        self.repo = StockBalanceD2DRepository(db)

    def lookup_item(self, item_id: int) -> StockItemLookup:
        raw = self.repo.lookup_item(item_id)
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item ID not found.",
            )
        iid = int(raw["item_id"])
        return StockItemLookup(
            item_id=iid,
            item_id_display=dash_item(iid),
            item_title=str(raw.get("item_title") or "").strip(),
            manualid=int(raw.get("manualid") or 0) or None,
        )

    def search_items(self, q: str) -> list[StockItemLookup]:
        return [
            StockItemLookup(
                item_id=int(r["item_id"]),
                item_id_display=dash_item(r["item_id"]),
                item_title=str(r.get("item_title") or "").strip(),
                manualid=int(r.get("manualid") or 0) or None,
            )
            for r in self.repo.search_items(q)
        ]

    def build_report(self, params: StockBalanceD2DRequest) -> StockBalanceD2DData:
        if params.date_to < params.date_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date range: From date must be on or before To date.",
            )

        start_id = 1 if params.complete_report else params.start_item_id
        end_id = MAX_ITEM_ID if params.complete_report else params.end_item_id

        raw_rows = self.repo.fetch_item_balances(
            start_id,
            end_id,
            params.date_from,
            params.date_to,
            store_ledger=params.store_ledger,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )
        if not raw_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Account ID in the selected Range.",
            )

        rows: list[StockBalanceD2DRow] = []
        totals = StockBalanceD2DTotals()
        print_amount = params.print_amount

        for raw in raw_rows:
            # --- Qty (VB6 qtytcbal / qtycdebit / qtyccredit / qtynetbal / qtynetclosing) ---
            oqty = float(raw.get("oqty") or 0)
            pre_qtydr = float(raw.get("pre_qtydr") or 0)
            pre_qtycr = float(raw.get("pre_qtycr") or 0)
            period_qtydr = float(raw.get("period_qtydr") or 0)
            period_qtycr = float(raw.get("period_qtycr") or 0)

            qty_opening = oqty + pre_qtydr - pre_qtycr
            qty_net = period_qtydr - period_qtycr
            qty_closing = qty_opening + qty_net

            # --- Amt (VB6 amttcbal / amtcdebit / amtccredit / amtnetbal / amtnetclosing) ---
            # Uses cost_amtdr / cost_amtcr from fin_ldgr
            oamt = float(raw.get("oamt") or 0)
            pre_amtdr = float(raw.get("pre_amtdr") or 0)
            pre_amtcr = float(raw.get("pre_amtcr") or 0)
            period_amtdr = float(raw.get("period_amtdr") or 0)
            period_amtcr = float(raw.get("period_amtcr") or 0)

            amt_opening = oamt + pre_amtdr - pre_amtcr
            amt_net = period_amtdr - period_amtcr
            amt_closing = amt_opening + amt_net

            if not _passes_zero_filter(
                qty_opening=qty_opening,
                qty_in=period_qtydr,
                qty_out=period_qtycr,
                qty_closing=qty_closing,
                suppress_zero=params.suppress_zero_bal,
            ):
                continue

            item_id = int(raw["item_id"])
            row = StockBalanceD2DRow(
                item_id=item_id,
                item_id_display=dash_item(item_id),
                item_title=str(raw.get("item_title") or "").strip(),
                brand=_brand_label(int(raw.get("manualid") or 0), params.show_manual_id),
                # Qty-mode columns
                opening_balance=qty_opening,
                stock_in=period_qtydr,
                stock_out=period_qtycr,
                net_balance=qty_net,
                closing_balance=qty_closing,
                # Amt-mode columns (RptStD2DAmtBrand)
                opening_qty=qty_opening,
                opening_amt=amt_opening,
                period_qty=qty_net,
                period_amt=amt_net,
                closing_qty=qty_closing,
                closing_amt=amt_closing,
            )
            rows.append(row)

            if print_amount:
                totals.opening_qty += qty_opening
                totals.opening_amt += amt_opening
                totals.period_qty += qty_net
                totals.period_amt += amt_net
                totals.closing_qty += qty_closing
                # Closing Amt footer = sum of all row closing amts (incl. negatives)
                totals.closing_amt += amt_closing
            else:
                totals.opening_balance += qty_opening
                totals.stock_in += period_qtydr
                totals.stock_out += period_qtycr
                if qty_net > 0:
                    totals.net_stock_in += qty_net
                elif qty_net < 0:
                    totals.net_stock_out += abs(qty_net)
                if qty_closing >= 0:
                    totals.closing_balance += qty_closing

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No records found for the selected period.",
            )

        criteria = (
            f"From: {start_id} To: {end_id} "
            f"From: {params.date_from.strftime('%d/%m/%Y')} "
            f"To: {params.date_to.strftime('%d/%m/%Y')}"
        )
        date_range = (
            f"From: {params.date_from.strftime('%d/%m/%Y')} "
            f"To: {params.date_to.strftime('%d/%m/%Y')}"
        )
        # VB6: amount title has no trailing period; qty title has one
        report_title = (
            "Stock Balance Date to Date"
            if print_amount
            else "Stock Balance Date to Date."
        )

        return StockBalanceD2DData(
            company_name=settings.company_name,
            report_title=report_title,
            criteria=criteria,
            date_range=date_range,
            printed_on=datetime.now().strftime("%d/%m/%Y"),
            print_amount=print_amount,
            rows=rows,
            total_rows=len(rows),
            totals=totals,
        )
