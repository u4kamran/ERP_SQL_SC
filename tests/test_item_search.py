from app.services.item_price_search_service import ItemPriceSearchService


def test_normalize_and_qty():
    assert ItemPriceSearchService.normalize_query("  dawn   bread  ") == "dawn bread"
    assert ItemPriceSearchService.normalize_query("I need dawn bread") == "dawn bread"
    qty, rest = ItemPriceSearchService.extract_qty("2 dawn bread")
    assert qty == 2.0
    assert rest == "dawn bread"
    qty2, rest2 = ItemPriceSearchService.extract_qty("2 liter milk")
    assert qty2 is None
    assert rest2.lower() == "milk"


def test_word_boundary():
    assert ItemPriceSearchService._has_phrase("oil", "dalda cooking oil")
    assert not ItemPriceSearchService._has_phrase("oil", "aluminum foil")
