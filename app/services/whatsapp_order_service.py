"""Professional chat order cart + receipt (sales prices only, never cost)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.config.settings import settings
from app.schemas.guest_price_lookup import GuestPriceLookupResponse, GuestPriceSearchMatch
from app.schemas.whatsapp_order import ChatOrder, ChatOrderSummary, OrderCartItem
from app.services import whatsapp_order_store as order_store
from app.services.guest_price_lookup_service import to_proper_case


class WhatsAppOrderService:
    @staticmethod
    def empty_order_context(
        *,
        customer_name: str = "",
        customer_mobile: str = "",
        customer_address: str = "",
        cart: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "mode": "order",
            "step": "browse",
            "cart": cart or [],
            "pending_item": None,
            "pending_options": [],
            "all_options": [],
            "page": 0,
            "customer_name": customer_name or "",
            "customer_mobile": customer_mobile or "",
            "customer_address": customer_address or "",
            "notes": "",
        }

    def item_from_lookup(
        self,
        item: GuestPriceLookupResponse | GuestPriceSearchMatch | dict[str, Any],
        qty: float = 1.0,
    ) -> OrderCartItem:
        if isinstance(item, dict):
            data = item
        else:
            data = item.model_dump()
        unit = float(data.get("sales_rate") or data.get("unit_price") or 0)
        gst = float(data.get("gst_amount") or 0)
        wo = data.get("sales_price_wo_gst")
        if wo is None:
            wo = data.get("price_wo_gst")
        wo_f = float(wo) if wo is not None else max(unit - gst, 0.0)
        qty = self._safe_qty(qty)
        title = to_proper_case(str(data.get("item_title") or "")) or str(
            data.get("item_title") or "Item"
        )
        short = to_proper_case(str(data.get("item_short") or "")) or ""
        uom = to_proper_case(str(data.get("uom_title") or "")) or ""
        return OrderCartItem(
            manual_id=int(data.get("manual_id") or 0),
            item_title=title,
            item_short=short or "",
            barcodeid=str(data.get("barcodeid") or ""),
            uom_title=uom or "",
            unit_price=unit,
            price_wo_gst=wo_f,
            gst_amount=gst,
            qty=qty,
            line_total=round(unit * qty, 2),
            line_gst=round(gst * qty, 2),
            line_wo_gst=round(wo_f * qty, 2),
        )

    def merge_into_cart(
        self,
        cart: list[dict[str, Any]],
        item: OrderCartItem,
    ) -> list[dict[str, Any]]:
        rows = list(cart or [])
        for row in rows:
            if int(row.get("manual_id") or 0) == item.manual_id:
                new_qty = self._safe_qty(float(row.get("qty") or 0) + item.qty)
                updated = self.item_from_lookup(
                    {
                        "manual_id": item.manual_id,
                        "item_title": item.item_title,
                        "item_short": item.item_short,
                        "barcodeid": item.barcodeid,
                        "uom_title": item.uom_title,
                        "sales_rate": item.unit_price,
                        "gst_amount": item.gst_amount,
                        "sales_price_wo_gst": item.price_wo_gst,
                    },
                    new_qty,
                )
                row.clear()
                row.update(updated.model_dump())
                return rows
        rows.append(item.model_dump())
        return rows

    def remove_from_cart(
        self,
        cart: list[dict[str, Any]],
        index: int,
    ) -> list[dict[str, Any]]:
        rows = list(cart or [])
        if 1 <= index <= len(rows):
            rows.pop(index - 1)
        return rows

    def totals(self, cart: list[dict[str, Any]]) -> dict[str, float | int]:
        items = [OrderCartItem(**row) for row in (cart or [])]
        return {
            "item_count": len(items),
            "qty_total": round(sum(i.qty for i in items), 2),
            "subtotal_wo_gst": round(sum(i.line_wo_gst for i in items), 2),
            "gst_total": round(sum(i.line_gst for i in items), 2),
            "order_total": round(sum(i.line_total for i in items), 2),
        }

    def format_cart(
        self,
        cart: list[dict[str, Any]],
        *,
        customer_name: str = "",
        customer_mobile: str = "",
        title: str = "ORDER DRAFT",
        footer: str = "",
    ) -> str:
        company = settings.company_name or settings.app_name
        totals = self.totals(cart)
        lines = [
            "══════════════════════════",
            f"  {company}",
            f"     {title}",
            "══════════════════════════",
        ]
        if customer_name:
            lines.append(f"Customer   {customer_name}")
        if customer_mobile:
            lines.append(f"Mobile     {customer_mobile}")
        lines.append("──────────────────────────")
        lines.append("ITEMS")
        lines.append("──────────────────────────")
        if not cart:
            lines.append("Cart is empty.")
        else:
            for idx, raw in enumerate(cart, start=1):
                item = OrderCartItem(**raw)
                unit = self._money(item.unit_price)
                line_total = self._money(item.line_total)
                qty = self._qty(item.qty)
                uom = f" · {item.uom_title}" if item.uom_title else ""
                lines.append(f"{idx}. {item.item_title}")
                lines.append(f"   Code {item.manual_id}{uom}")
                lines.append(f"   {qty} × Rs {unit}")
                lines.append(f"                 Rs {line_total}")
        lines.append("──────────────────────────")
        lines.append(f"Subtotal (ex-GST)  Rs {self._money(float(totals['subtotal_wo_gst']))}")
        lines.append(f"GST                Rs {self._money(float(totals['gst_total']))}")
        lines.append("──────────────────────────")
        lines.append(f"ORDER TOTAL        Rs {self._money(float(totals['order_total']))}")
        lines.append("══════════════════════════")
        lines.append(
            f"Lines: {totals['item_count']}  ·  Qty: {self._qty(float(totals['qty_total']))}"
        )
        if footer:
            lines.append(footer)
        return "\n".join(lines)

    def format_confirmed_receipt(self, order: dict[str, Any] | ChatOrder) -> str:
        if isinstance(order, ChatOrder):
            data = order.model_dump()
        else:
            data = order
        company = settings.company_name or settings.app_name
        created = data.get("created_at") or ""
        if isinstance(created, datetime):
            created_txt = created.strftime("%d %b %Y %H:%M")
        else:
            try:
                created_txt = datetime.fromisoformat(str(created)).strftime("%d %b %Y %H:%M")
            except ValueError:
                created_txt = str(created)[:16]
        cart = data.get("items") or []
        return self._build_receipt(company, data, cart, created_txt)

    def _build_receipt(
        self,
        company: str,
        data: dict[str, Any],
        cart: list[Any],
        created_txt: str,
    ) -> str:
        lines = [
            "══════════════════════════",
            f"  {company}",
            "   OFFICIAL ORDER RECEIPT",
            "══════════════════════════",
            f"Order No.  {data.get('order_no')}",
            f"Date       {created_txt}",
            f"Customer   {data.get('customer_name') or 'Guest'}",
            f"Mobile     {data.get('customer_mobile') or data.get('phone') or '—'}",
            f"Channel    {(data.get('channel') or '').title() or '—'}",
        ]
        if data.get("customer_address"):
            lines.append(f"Address    {data['customer_address']}")
        lat = data.get("latitude")
        lng = data.get("longitude")
        maps = data.get("maps_url") or ""
        if lat is not None and lng is not None:
            lines.append(f"GPS        {lat}, {lng}")
        if maps:
            lines.append(f"Maps       {maps}")
        if data.get("notes"):
            lines.append(f"Notes      {data['notes']}")
        lines.append("──────────────────────────")
        lines.append("ITEMS")
        lines.append("──────────────────────────")
        norm_cart = []
        for item in cart:
            norm_cart.append(item if isinstance(item, dict) else item.model_dump())
        for idx, raw in enumerate(norm_cart, start=1):
            item = OrderCartItem(**raw)
            lines.append(f"{idx}. {item.item_title}")
            uom = f" · {item.uom_title}" if item.uom_title else ""
            lines.append(f"   Code {item.manual_id}{uom}")
            lines.append(
                f"   {self._qty(item.qty)} × Rs {self._money(item.unit_price)}"
            )
            lines.append(f"                 Rs {self._money(item.line_total)}")
        totals = self.totals(norm_cart)
        lines.append("──────────────────────────")
        lines.append(
            f"Subtotal (ex-GST)  Rs {self._money(float(totals['subtotal_wo_gst']))}"
        )
        lines.append(f"GST                Rs {self._money(float(totals['gst_total']))}")
        lines.append("──────────────────────────")
        lines.append(
            f"ORDER TOTAL        Rs {self._money(float(totals['order_total']))}"
        )
        lines.append("══════════════════════════")
        lines.append(f"Status: {(data.get('status') or 'pending').upper()}")
        lines.append("Thank you. Our team will confirm stock")
        lines.append("and arrange pickup / delivery shortly.")
        lines.append("Reply MENU for main menu.")
        return "\n".join(lines)

    def confirm_order(
        self,
        *,
        conversation: dict[str, Any],
        context: dict[str, Any],
    ) -> ChatOrder:
        cart = list(context.get("cart") or [])
        if not cart:
            raise ValueError("Cart is empty.")
        totals = self.totals(cart)
        now = datetime.utcnow()
        order = {
            "order_id": str(uuid.uuid4()),
            "order_no": order_store.next_order_no(),
            "conversation_id": conversation.get("conversation_id") or "",
            "channel": conversation.get("channel") or "offline",
            "phone": conversation.get("phone") or "",
            "customer_name": context.get("customer_name")
            or conversation.get("display_name")
            or "Guest",
            "customer_mobile": context.get("customer_mobile")
            or conversation.get("phone")
            or "",
            "customer_address": context.get("customer_address") or "",
            "latitude": context.get("latitude"),
            "longitude": context.get("longitude"),
            "maps_url": context.get("maps_url") or "",
            "notes": context.get("notes") or "",
            "status": "pending",
            "items": cart,
            "item_count": int(totals["item_count"]),
            "subtotal_wo_gst": float(totals["subtotal_wo_gst"]),
            "gst_total": float(totals["gst_total"]),
            "order_total": float(totals["order_total"]),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "receipt_text": "",
        }
        lat = order.get("latitude")
        lng = order.get("longitude")
        if lat is not None and lng is not None and not order.get("maps_url"):
            order["maps_url"] = (
                f"https://www.google.com/maps?q={float(lat)},{float(lng)}"
            )
        order["receipt_text"] = self.format_confirmed_receipt(order)
        saved = order_store.save_order(order)
        return ChatOrder(**saved)

    def list_orders(self, status: str | None = None) -> list[ChatOrderSummary]:
        rows = order_store.list_orders(status=status, limit=100)
        out = []
        for row in rows:
            out.append(
                ChatOrderSummary(
                    order_id=row["order_id"],
                    order_no=row.get("order_no") or "",
                    channel=row.get("channel") or "offline",
                    phone=row.get("phone") or "",
                    customer_name=row.get("customer_name") or "",
                    customer_mobile=row.get("customer_mobile") or "",
                    status=row.get("status") or "pending",
                    item_count=int(row.get("item_count") or 0),
                    order_total=float(row.get("order_total") or 0),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return out

    def get_order(self, order_id: str) -> ChatOrder:
        row = order_store.get_order(order_id)
        if not row:
            raise KeyError(order_id)
        return ChatOrder(**row)

    def set_status(self, order_id: str, status: str) -> ChatOrder:
        return ChatOrder(**order_store.update_order_status(order_id, status))

    @staticmethod
    def pending_count() -> int:
        return order_store.pending_count()

    @staticmethod
    def _safe_qty(qty: float) -> float:
        try:
            value = float(qty)
        except (TypeError, ValueError):
            value = 1.0
        if value <= 0:
            value = 1.0
        if value > 9999:
            value = 9999
        # Keep integers clean
        if abs(value - round(value)) < 1e-9:
            return float(int(round(value)))
        return round(value, 2)

    @staticmethod
    def _money(value: float | None) -> str:
        if value is None:
            return "0"
        number = float(value)
        if abs(number - int(number)) < 1e-9:
            return f"{int(number):,}"
        return f"{number:,.2f}"

    @staticmethod
    def _qty(value: float) -> str:
        if abs(value - int(value)) < 1e-9:
            return str(int(value))
        return f"{value:.2f}"
