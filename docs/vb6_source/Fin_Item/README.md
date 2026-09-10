# Fin_Item (Item Info) — VB6 source notes

Source copied from:
`E:\AccesToSQL_Barcode_20130316 - SI_BC_AutoInv_WholeSaleQty_V1_JanDec\Fin_Item.frm`

## Form metrics (twips → ≈px at /15)

| Property | Twips | ≈ px |
|----------|------:|-----:|
| ClientWidth | 7965 | 531 |
| ClientHeight | 9255 | 617 |
| BackColor | `&H00C0C0C0&` | `#C0C0C0` |
| Banner / Status labels | `&H00C98A45&` | `#458AC9` |
| Status values | `&H00F2CD6C&` | `#6CCDF2` |
| Title / RO captions FG | `&H00800000&` | `#000080` |
| Title / RO captions BG | `&H00E0E0E0&` | `#E0E0E0` |

Banner: `Line2` Caption **Item Info** (Arial Black 15.75 italic).  
Status strip: Status / LblStatus / Records / TxtRecCount / Last ID / TxtLastID.
SSTab default `Tab = 3` → **Last Purchases**.  
Store frame: Promotion checkbox maps to DB `critical_level1` (TxtCritical_Level1 is Visible=False).

## Key field Y positions (≈px)

| Row | ≈Top | Controls |
|-----|------:|----------|
| Item | 70 | TxtID, TxtTitle |
| Short/OEM | 93 | TxtShortName, TxtOEM |
| Manual/Barcode | 117 | txtManualID, chkFocusManBar, txtBarcodeID |
| UOM/WS | 140 | TxtUOMID, TxtUOMTitle, txtWSBarcodeid |
| Nature/Country | 162 | CboNature, TxtCountryID, LblCountryTitle |
| Min/Max | 185 | TxtMin_Level, TxtMax_Level |
| Reorder/Critical | 209 | TxtRO_Qty, TxtCritical_Level, ChkEDStatus |
| Store frame | 231 | Frame1 Store Stock Levels (H≈64) |
| Pricing | 296+ | Cost/Sales/WS … Company |
| Buttons | 586 | Save Clear Delete Category View ID Manual Close (75×25) |

See `controls_geometry.tsv` for full dump.
