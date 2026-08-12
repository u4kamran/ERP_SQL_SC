"""Paste-JSON import helpers — parsing, field picking, manual-ID titles."""

import pytest
from fastapi import HTTPException

from app.services.purchase_automation_service import (
    _item_title_with_manual,
    _num,
    _parse_json_text,
    _pick,
    _pick_items,
)

SAMPLE = """
{
  "invoice_no": "301",
  "reference_no": "7957",
  "date": "2026-08-07",
  "customer": "CHENAB STEEL LAHORE",
  "items": [
    {"line": 1, "manual_id": "47", "description": "Lance Pipe SS", "qty": 3, "uom": "P",
     "rate": 1000, "amount": 3000, "status": "Verified"},
    {"line": 7, "manual_id": "221", "description": "Calcium Silicon", "qty": 51.48, "uom": "KG",
     "rate": 1300, "amount": 66924, "status": "Verified"}
  ],
  "totals": {"gross_amount": 481960, "net_amount": 481960}
}
"""


def test_parse_json_text_reads_sample():
    payload = _parse_json_text(SAMPLE)
    assert payload["invoice_no"] == "301"
    assert len(_pick_items(payload)) == 2


def test_parse_json_text_strips_code_fence():
    payload = _parse_json_text('```json\n{"items": [{"manual_id": "47"}]}\n```')
    assert _pick_items(payload)[0]["manual_id"] == "47"


def test_parse_bare_array_becomes_items():
    payload = _parse_json_text('[{"manual_id": "5", "qty": 2, "rate": 10}]')
    assert len(_pick_items(payload)) == 1


def test_invalid_json_raises_400():
    with pytest.raises(HTTPException) as exc:
        _parse_json_text("{not json")
    assert exc.value.status_code == 400


def test_pick_is_case_insensitive_and_skips_blanks():
    row = {"Manual_ID": "", "manualid": "179", "Description": "Temperature Rod"}
    assert _pick(row, "manual_id", "manualid") == "179"
    assert _pick(row, "description") == "Temperature Rod"
    assert _pick(row, "missing") is None


def test_num_handles_thousands_separators_and_blanks():
    assert _num("66,924") == 66924.0
    assert _num(None) == 0.0
    assert _num("abc") == 0.0


def test_item_title_always_carries_manual_id():
    assert _item_title_with_manual({"item_title": "Lance Pipe SS", "manualid": 47.0}) == "Lance Pipe SS --- 47"
    assert _item_title_with_manual({"item_title": "K-90", "manualid": None}) == "K-90"


def test_qty_rate_drives_amount_when_json_amount_wrong():
    item = _pick_items(_parse_json_text(SAMPLE))[1]
    qty, rate = _num(item["qty"]), _num(item["rate"])
    assert round(qty * rate, 2) == 66924.0
