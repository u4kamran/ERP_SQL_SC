# Item Search Performance

Target: autocomplete under ~300ms after 200–300ms debounce.

## Approach

- Browser never loads the item master.
- SQL `SELECT TOP n` with parameterized `LIKE` prefix (`dawn%`) plus contains (`%dawn%`).
- Candidate scoring is in-process on the small result set, not the full table.
- Fuzzy matching runs only when indexed search returns fewer than 3 rows.
- Autocomplete maps SQL columns directly (no per-row `lookup_manual_id` round trip).

## Indexes (created if missing)

- `IX_FIN_ITEM_TITLE` on `ITEM_TITLE` (helps prefix `LIKE 'dawn%'`)
- `IX_FIN_ITEM_BARCODE` on `barcodeid`

If index creation is skipped (lock/size), search still works; prefix may be slower.

Measured on this ERP `FIN_ITEM` (LAN, after Co join):

| Query | Approx |
| --- | --- |
| `dawn` | ~300–350 ms |
| `milk` / `fauji` / `choco` | ~280–300 ms |
| `bread dawn` / alias `biscut` | ~550–610 ms |
| exact barcode | ~80 ms |

## Rate limit

45 requests per IP per 60 seconds on public search endpoints.

## Measure

After deploy, time:

```text
GET /api/v1/public/price-lookup/search?q=dawn
```

from the ERP host. Typical LAN SQL for TOP 40 on an indexed title is well under 300ms. If not, inspect actual execution plan on `FIN_ITEM` before adding another engine.
