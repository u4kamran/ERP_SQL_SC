# Item Image Manager — Pakistani Product Finder

Separate module. **`FIN_ITEM` is read-only.**

## Primary providers (PK)

| Provider | Status | Access |
| --- | --- | --- |
| **Naheed** | Live | Public storefront GraphQL (`/graphql`) — not `/catalogsearch` (robots.txt disallows) |
| **METRO** | Live | Typesense search on `admin.metro-online.pk` (storefront auth headers) |
| Carrefour | Stub | Enable when integration is ready |
| Imtiaz | Stub | Enable when integration is ready |
| Al-Fatah | Stub | Enable when integration is ready |

Optional fallbacks (off by default): Open Food Facts, UPCitemdb.

## Search levels

1. Exact barcode  
2. Barcode + item name  
3. Exact item name  
4. Normalized name (KG/GM/ML/L/PCS — search only, never written to `FIN_ITEM`)

## Matching

- Exact barcode +60, name +20, brand +10, pack +10  
- **Hard reject** on pack mismatch (e.g. 1 KG vs 500 GM)  
- Thresholds: 90 auto, 75 review, 50 minimum candidate  

## Setup

```bat
.\venv\Scripts\python.exe scripts\setup_item_images.py --site erp
```

Runs `sql/31_*` tables + `sql/33_*` PK provider settings.

Admin UI: `/admin/item-images`

## API

`/api/v1/inventory/item-images`
