from app.services.guest_price_lookup_service import is_hidden_shop_title
from app.services.whatsapp_shop_service import (
    is_shop_nav_message,
    parse_area_line,
    parse_fulfill,
    parse_hub_action,
    parse_open_category,
    parse_sub_index,
)


def test_is_hidden_shop_title():
    assert is_hidden_shop_title("Empty Bottle")
    assert is_hidden_shop_title("empty crate")
    assert is_hidden_shop_title("  EMPTY X")
    assert not is_hidden_shop_title("Dalda Oil")
    assert not is_hidden_shop_title("Bottle Empty")
    assert not is_hidden_shop_title("")


def test_is_shop_nav_message():
    assert is_shop_nav_message("CATEGORIES", shop_view="products")
    assert is_shop_nav_message("CAT 1090000000 Dairy", shop_view="categories")
    assert not is_shop_nav_message("bread", shop_view="products")


def test_parse_open_category():
    assert parse_open_category("CAT 1090000000 Dairy") == (1090000000, "Dairy")
    assert parse_open_category("hello") is None
    assert parse_sub_index("S2") == 2


def test_parse_fulfill():
    assert parse_fulfill("1") == "delivery"
    assert parse_fulfill("pickup") == "pickup"
    assert parse_fulfill("hello") is None


def test_parse_area_line():
    assert parse_area_line("Lahore, Shad Bagh") == ("Lahore", "Shad Bagh")
    assert parse_area_line("x") is None


def test_hub_digits_only_on_hub():
    assert parse_hub_action("1", shop_view="hub") == "categories"
    assert parse_hub_action("1", shop_view="products") is None
    assert parse_hub_action("categories", shop_view="products") == "categories"
    assert parse_hub_action("clear search", shop_view="products") == "clear_search"
    assert parse_hub_action("4", shop_view="hub") == "cart"
