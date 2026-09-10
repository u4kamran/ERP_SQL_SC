# Item Search Test Report

Backup before work: `D:\CursorProject\backups\ahsteellab-nsds2626-2026-08-18`

Automated:

```bash
venv\Scripts\python.exe -m pytest tests\test_item_search.py -q
```

| Case | Expected |
| --- | --- |
| `dawn` | Ranked DAWN* titles, prefix first |
| `bread dawn` | Token match, order independent |
| `8945590006000` | Exact barcode when that barcode exists in `FIN_ITEM` |
| `2 dawn bread` | suggested_qty=2, search=dawn bread |
| `2 liter milk` | Not treated as qty=2; searches milk |
| `biscut` / `talbena` / `doodh` | Alias expansion |
| Empty / 1 char (if min=2) | No query |
| ADD from suggestion | Cart line via `ADDITEM {manual_id}` |
| Existing chat menus 1–6 | Unchanged |

Manual: open `/guest/chat`, complete OTP if required, type item names and barcodes, add to cart, confirm existing order save still works.
