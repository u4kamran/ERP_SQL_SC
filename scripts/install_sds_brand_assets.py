"""Install official Shafique Departmental Store lockup and icons into ERP."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ERP = Path(r"D:\CursorProject\ahsteellab-nsds2626\app\static\img")
ASSETS = Path(r"C:\Users\ShahNaseer\.cursor\projects\d-CursorProject-ahsteellab-nsds2626\assets")

LOCKUP = ASSETS / "c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_image-fbbb6674-df08-43da-854f-f5ac55640afe.png"
ICON_ONLY = ASSETS / "c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_image-3d1e420d-baef-4da5-8ec2-3f40bc7efd7d.png"
APP_ICON = ASSETS / "c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_image-759cbc75-1125-44be-bd1e-0d4e4594030d.png"


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


def _square_pad(im: Image.Image, size: int) -> Image.Image:
    src = im.convert("RGBA")
    src.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    x = (size - src.width) // 2
    y = (size - src.height) // 2
    canvas.paste(src, (x, y), src)
    return canvas


def main() -> None:
    ERP.mkdir(parents=True, exist_ok=True)
    lockup = Image.open(LOCKUP).convert("RGBA")
    lockup.save(ERP / "sds-logo.png", optimize=True)

    mark = _trim_light(_drop_caption(Image.open(ICON_ONLY).convert("RGBA")))
    mark.save(ERP / "sds-icon.png", optimize=True)

    app = _trim_light(_drop_caption(Image.open(APP_ICON).convert("RGBA")))
    app.save(ERP / "sds-app-icon.png", optimize=True)

    for size in (16, 32, 48, 64, 180, 192, 512):
        _square_pad(app, size).save(ERP / f"sds-icon-{size}.png", optimize=True)

    Image.open(ERP / "sds-icon-32.png").save(ERP / "favicon.png")
    Image.open(ERP / "sds-icon-192.png").save(ERP / "sds-favicon.png")
    print("lockup", lockup.size, "mark", mark.size, "app", app.size)
    print("Installed Shafique assets in", ERP)


if __name__ == "__main__":
    main()
