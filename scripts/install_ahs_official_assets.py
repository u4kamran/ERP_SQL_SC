"""Install official Al Haram Steel Lab lockup and app icon into ARP."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ARP = Path(r"D:\CursorProject\ahsteellab-arp\app\static\img\brand")
ASSETS = Path(r"C:\Users\ShahNaseer\.cursor\projects\d-CursorProject-ahsteellab-nsds2626\assets")

LOCKUP_3D = ASSETS / "c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_image-f8b5b491-843a-4893-ae8c-9cd6fa76a2a8.png"
LOCKUP_FLAT = ASSETS / "c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_image-aff450e0-bb04-4144-8394-ca12a2f01f8f.png"
APP_ICON = ASSETS / "c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_image-78abc96c-0c95-49c5-a077-9c6bab644988.png"


def _blue_rows(im: Image.Image) -> list[bool]:
    rgba = im.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()
    rows = []
    for y in range(h):
        blue = 0
        for x in range(w):
            r, g, b, _a = pixels[x, y]
            if b > r + 15 and b > 70:
                blue += 1
        rows.append(blue >= 8)
    return rows


def _drop_caption(im: Image.Image) -> Image.Image:
    """Keep the graphic; drop the APP ICON / FAVICON caption under it."""
    flags = _blue_rows(im)
    h = len(flags)
    y = h - 1
    while y >= 0 and not flags[y]:
        y -= 1
    while y >= 0 and flags[y]:
        y -= 1
    caption_top = y + 1
    if caption_top <= int(h * 0.70):
        return im
    while y >= 0 and not flags[y]:
        y -= 1
    return im.crop((0, 0, im.width, max(1, y + 2)))


def _trim_light(im: Image.Image, limit: int = 248) -> Image.Image:
    rgba = im.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()
    left, top, right, bottom = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 8 and (r + g + b) / 3 < limit:
                found = True
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)
    if not found:
        return im
    pad = 2
    return im.crop((
        max(0, left - pad),
        max(0, top - pad),
        min(w, right + pad + 1),
        min(h, bottom + pad + 1),
    ))


def _square_pad(im: Image.Image, size: int, bg=(255, 255, 255, 255)) -> Image.Image:
    src = im.convert("RGBA")
    src.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), bg)
    x = (size - src.width) // 2
    y = (size - src.height) // 2
    canvas.paste(src, (x, y), src)
    return canvas


def main() -> None:
    ARP.mkdir(parents=True, exist_ok=True)
    lockup = Image.open(LOCKUP_3D).convert("RGBA")
    lockup.save(ARP / "ahs-logo.png", optimize=True)
    Image.open(LOCKUP_FLAT).convert("RGBA").save(ARP / "ahs-logo-print.png", optimize=True)

    app = _trim_light(_drop_caption(Image.open(APP_ICON).convert("RGBA")))
    app.save(ARP / "ahs-app-icon.png", optimize=True)
    app.save(ARP / "ahs-favicon.png", optimize=True)

    for size in (16, 32, 48, 64, 180, 192, 512):
        _square_pad(app, size).save(ARP / f"ahs-icon-{size}.png", optimize=True)

    Image.open(ARP / "ahs-icon-180.png").save(ARP / "apple-touch-icon.png")
    Image.open(ARP / "ahs-icon-192.png").save(ARP / "android-chrome-192x192.png")
    Image.open(ARP / "ahs-icon-512.png").save(ARP / "android-chrome-512x512.png")
    Image.open(ARP / "ahs-icon-32.png").save(ARP / "favicon-32x32.png")
    Image.open(ARP / "ahs-icon-16.png").save(ARP / "favicon-16x16.png")
    print("lockup", lockup.size, "app", app.size)
    print("Installed Al Haram assets in", ARP)


if __name__ == "__main__":
    main()
