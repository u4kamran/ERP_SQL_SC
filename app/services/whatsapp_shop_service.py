"""Category browse + cart validation for WhatsApp / guest chat.

Reuses PublicCatalogService. Does not invent prices, stock, or delivery fees.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException

from app.schemas.public_catalog import (
    CartValidateLineIn,
    CartValidateRequest,
    PublicProduct,
)
from app.services.guest_price_lookup_service import is_hidden_shop_title
from app.services.public_catalog_service import PublicCatalogService
from app.services.whatsapp_order_service import WhatsAppOrderService

SHOP_PAGE_SIZE = 8
CATEGORY_PAGE_SIZE = 20

def parse_open_category(text: str) -> tuple[int, str] | None:
    raw = (text or "").strip()
    match = re.fullmatch(r"(?i)cat(?:egory)?\s+(\d{3,})(?:\s+(.+))?", raw)
    if not match:
        return None
    title = (match.group(2) or "").strip()
    return int(match.group(1)), title


def parse_sub_index(text: str) -> int | None:
    match = re.fullmatch(r"(?i)s(\d{1,2})", (text or "").strip())
    if not match:
        return None
    return int(match.group(1))


def cart_qty_total(cart: list[dict[str, Any]]) -> float:
    return sum(float(row.get("qty") or 0) for row in cart or [])


def shop_cart_hint(context: dict[str, Any]) -> str:
    cart = list(context.get("cart") or [])
    qty = cart_qty_total(cart)
    if qty <= 0:
        return ""
    orders = WhatsAppOrderService()
    totals = orders.totals(cart)
    label = int(qty) if abs(qty - int(qty)) < 1e-9 else qty
    money = orders._money(float(totals.get("order_total") or 0))
    return f"Cart: *{label}* · *Rs {money}* — tap View cart for details."


def parse_hub_action(lower: str, *, shop_view: str) -> str | None:
    """Main shop actions. Digits 1–4 only apply on the shop hub (not on a numbered list)."""
    if lower in {
        "categories",
        "category",
        "cat",
        "shop by category",
        "browse",
    }:
        return "categories"
    if lower in {"offers", "offer", "promo", "promotions"}:
        return "offers"
    if lower in {"search", "search products", "find"}:
        return "search"
    if lower in {"shop", "shopping", "hub"}:
        return "hub"
    if lower in {"back", "previous", "prev"}:
        return "back"
    if lower in {"clear search", "clearsearch", "reset search"}:
        return "clear_search"
    if shop_view in {"", "hub"} and lower in {"1", "categories"}:
        return "categories"
    if shop_view in {"", "hub"} and lower in {"2"}:
        return "search"
    if shop_view in {"", "hub"} and lower in {"3"}:
        return "offers"
    if shop_view in {"", "hub"} and lower in {"4"}:
        return "cart"
    return None


def is_shop_nav_message(text: str, *, shop_view: str = "") -> bool:
    """True when the customer is using shop browse controls (not free-text product search)."""
    raw = (text or "").strip()
    lower = raw.lower()
    if parse_open_category(raw) or parse_sub_index(raw):
        return True
    if parse_hub_action(lower, shop_view=shop_view):
        return True
    if lower in {"more", "next", "cart", "menu"}:
        return True
    if shop_view in {"categories", "products", "offers"} and re.fullmatch(
        r"\d{1,2}", lower
    ):
        return True
    return False


def parse_fulfill(lower: str) -> str | None:
    if lower in {"1", "delivery", "deliver"}:
        return "delivery"
    if lower in {"2", "pickup", "pick-up", "pick up", "collect"}:
        return "pickup"
    return None


def parse_area_line(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if len(raw) < 2:
        return None
    if "," in raw:
        city, area = raw.split(",", 1)
        city, area = city.strip(), area.strip()
        if city and area:
            return city[:80], area[:80]
    parts = raw.split()
    if len(parts) >= 2:
        return parts[0][:80], " ".join(parts[1:])[:80]
    return None


def product_to_shop_row(product: PublicProduct) -> dict[str, Any]:
    data = product.model_dump()
    data["kind"] = "product"
    return data


def category_to_shop_row(category_id: int, title: str) -> dict[str, Any]:
    return {
        "kind": "category",
        "category_id": int(category_id),
        "manual_id": 0,
        "item_title": title,
        "sales_rate": None,
        "barcodeid": "",
        "co_title": "",
        "in_stock": True,
    }


class WhatsAppShopService:
    def __init__(self, db):
        self.db = db
        self.catalog = PublicCatalogService(db) if db is not None else None

    def list_categories(
        self,
        parent_id: int | None,
        page: int,
        page_size: int = CATEGORY_PAGE_SIZE,
    ) -> dict[str, Any]:
        if self.catalog is None:
            return {"items": [], "has_more": False, "page": 1}
        page = max(int(page or 1), 1)
        size = max(int(page_size or CATEGORY_PAGE_SIZE), 1)
        raw = self.catalog.list_categories(parent_id=parent_id).items
        start = (page - 1) * size
        chunk = raw[start : start + size]
        rows = [category_to_shop_row(c.category_id, c.title) for c in chunk]
        return {
            "items": rows,
            "has_more": start + size < len(raw),
            "page": page,
            "total": len(raw),
        }

    def list_products(
        self,
        *,
        category_id: int | None,
        q: str | None,
        page: int,
        promo_only: bool = False,
    ) -> dict[str, Any]:
        if self.catalog is None:
            return {"items": [], "has_more": False, "page": 1}
        page = max(int(page or 1), 1)
        result = self.catalog.list_products(
            page=page,
            page_size=SHOP_PAGE_SIZE,
            promo_only=promo_only,
            q=q,
            category_id=category_id,
        )
        rows = [
            product_to_shop_row(item)
            for item in result.items
            if not is_hidden_shop_title(item.item_title)
        ]
        return {
            "items": rows,
            "has_more": bool(result.has_more),
            "page": result.page,
        }

    def lookup_product(self, manual_id: int) -> PublicProduct | None:
        if self.catalog is None or manual_id <= 0:
            return None
        try:
            product = self.catalog.lookup_manual_id(manual_id)
        except HTTPException:
            return None
        if product is None or is_hidden_shop_title(product.item_title):
            return None
        return product

    def validate_cart_lines(
        self,
        cart: list[dict[str, Any]],
        orders: WhatsAppOrderService,
    ) -> tuple[list[dict[str, Any]], list[str], bool]:
        """Re-price from ERP. Returns (cart, messages, ready_to_confirm)."""
        if self.catalog is None:
            return list(cart or []), ["Catalog is temporarily unavailable."], False
        lines_in = []
        for row in cart or []:
            mid = int(row.get("manual_id") or 0)
            qty = float(row.get("qty") or 0)
            if mid > 0 and qty > 0:
                lines_in.append(CartValidateLineIn(manual_id=mid, qty=qty))
        if not lines_in:
            return [], ["Your cart is empty."], False
        result = self.catalog.validate_cart(CartValidateRequest(lines=lines_in))
        messages: list[str] = []
        if result.message:
            messages.append(result.message)
        new_cart: list[dict[str, Any]] = []
        blocked = False
        for line in result.lines:
            if line.message:
                messages.append(f"{line.item_title or line.manual_id}: {line.message}")
            if not line.ok or line.qty <= 0:
                blocked = True
                continue
            updated = orders.item_from_lookup(
                {
                    "manual_id": line.manual_id,
                    "item_title": line.item_title,
                    "item_short": line.item_short,
                    "barcodeid": line.barcodeid,
                    "uom_title": line.uom_title,
                    "sales_rate": line.unit_price,
                    "gst_amount": line.gst_amount,
                    "sales_price_wo_gst": line.sales_price_wo_gst,
                },
                line.qty,
            )
            new_cart.append(updated.model_dump())
        ready = (not blocked) and bool(new_cart)
        return new_cart, messages, ready
