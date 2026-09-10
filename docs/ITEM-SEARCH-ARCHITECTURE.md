# Item Search Architecture

Live product autocomplete for Web WhatsApp (`/guest/chat`) over existing `dbo.FIN_ITEM`.

No paid search engine. No duplicate item master.

## Flow

```text
Type in chat box
  → 250ms debounce
  → GET /api/v1/public/price-lookup/search?q=
  → SQL Server ranked candidates (FIN_ITEM)
  → Top 10 suggestions
  → ADD → ADDITEM {manual_id}
  → existing WhatsApp order cart
```

## Ranking

1. Exact barcode / WS barcode / manual ID / item ID  
2. Exact title / short name  
3. Title prefix  
4. Word prefix  
5. All tokens (any order)  
6. Brand (`co_TITLE`)  
7. Alias expansion (`item_search_alias`)  
8. Fuzzy (`difflib`) only if fewer than 3 indexed hits  

Company/brand is `Co.co_title` joined on `FIN_ITEM.co_id` (not a column on `FIN_ITEM`).

## Database

| Object | Role |
| --- | --- |
| `FIN_ITEM` | Item master (source of truth) |
| `item_search_alias` | Alias → expand text |
| `item_search_log` | Anonymous search analytics |

Optional indexes: `IX_FIN_ITEM_TITLE`, `IX_FIN_ITEM_BARCODE`.

## API

| Endpoint | Use |
| --- | --- |
| `GET /api/v1/public/price-lookup/search` | Web WhatsApp autocomplete |
| `GET /api/v1/public/catalog/search` | Customer app autocomplete |
| `GET /api/v1/public/price-lookup/search-config` | min chars / debounce / max results |
| `GET /api/v1/marketing/item-search/dashboard` | Admin |

Queries are parameterized. Rate limit: 45 searches / IP / minute.

## UI

Suggestions overlay on the existing chat composer. Arrow keys, Enter, Esc. ADD uses the existing cart (`WhatsAppOrderService`).

## Settings file

`data/item_search_control.json` — min_chars, max_results, debounce_ms, fuzzy/alias/barcode flags.
