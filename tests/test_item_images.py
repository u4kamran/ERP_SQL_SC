"""Unit tests for item image scoring and normalization (no DB / network)."""

from app.services.item_images.normalization import extract_pack_size, pack_sizes_compatible
from app.services.item_images.providers.base import ImageCandidate, ItemSearchContext, ProductCandidate
from app.services.item_images.providers.metro_auth import metro_auth_headers
from app.services.item_images.scoring import decide_status, score_candidate, score_product


def test_exact_barcode_and_name_auto_accepts():
    ctx = ItemSearchContext(
        item_id=10001,
        item_title="Surf Excel 1 KG",
        barcodeid="8964001234567",
        brand="Unilever",
    )
    cand = ImageCandidate(
        image_url="https://example.com/a.jpg",
        product_title="Surf Excel 1 KG",
        product_brand="Unilever",
        product_barcode="8964001234567",
        source_name="naheed",
    )
    result = score_candidate(ctx, cand)
    assert not result.hard_reject
    assert result.score >= 90
    assert decide_status(result.score) == "AUTO_APPROVED"


def test_pack_size_mismatch_hard_rejects():
    ctx = ItemSearchContext(item_id=1, item_title="Surf Excel 1 KG")
    cand = ProductCandidate(
        provider="naheed",
        image_url="https://example.com/a.jpg",
        product_name="Surf Excel 500 GM",
    )
    result = score_product(ctx, cand)
    assert result.hard_reject
    assert result.reason == "pack_size_mismatch"


def test_barcode_mismatch_still_allows_name_review():
    ctx = ItemSearchContext(item_id=1, item_title="Surf Excel 1 KG", barcodeid="8964001234567")
    cand = ImageCandidate(
        image_url="https://example.com/a.jpg",
        product_title="Surf Excel 1 KG",
        product_barcode="9999999999999",
        source_name="naheed",
    )
    result = score_candidate(ctx, cand)
    assert not result.hard_reject
    assert 15 <= result.score <= 45


def test_decide_status_thresholds():
    assert decide_status(95) == "AUTO_APPROVED"
    assert decide_status(80) == "REVIEW_RECOMMENDED"
    assert decide_status(55) == "NEEDS_REVIEW"
    assert decide_status(30) == "NO_RELIABLE_MATCH"


def test_extract_pack_kg_to_grams():
    pack = extract_pack_size("Surf Excel 1 KG")
    assert pack is not None
    assert pack.unit == "g"
    assert pack.value == 1000.0


def test_naheed_name_only_match_reaches_review():
    ctx = ItemSearchContext(item_id=1, item_title="SURF EXCEL 1kg", barcodeid="8961014264814")
    cand = ProductCandidate(
        provider="naheed",
        image_url="https://example.com/a.jpg",
        product_name="Surf Excel With Deep Action Tecnology, 1KG",
    )
    result = score_product(ctx, cand)
    assert not result.hard_reject
    assert result.score >= 50


def test_metro_auth_header_format():
    headers = metro_auth_headers("get", "t_search")
    assert "bdz-playback-state" in headers
    state = headers["bdz-playback-state"]
    assert "_" in state
    ts, digest = state.split("_", 1)
    assert ts.isdigit()
    assert len(digest) == 32


def test_pack_compatible_same_size():
    ok, both = pack_sizes_compatible("Surf Excel 1 KG", "Surf Excel 1000 GM")
    assert both
    assert ok
