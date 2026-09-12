"""Install official KUMASHI logo assets into the NEW project only."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

SRC_PRIMARY = Path(
    r"C:\Users\ShahNaseer\.cursor\projects\d-CursorProject-ahsteellab-nsds2626\assets"
    r"\c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"008dc14922f1584edd6dd670d9773b9d_images_KUMASHI-a77f9881-2a3d-483e-90a4-98f7db7e00cf.png"
)
# Brand kit sheet (reference retained; primary mark used for app assets).
SRC_KIT = Path(
    r"C:\Users\ShahNaseer\.cursor\projects\d-CursorProject-ahsteellab-nsds2626\assets"
    r"\c__Users_ShahNaseer_AppData_Roaming_Cursor_User_workspaceStorage_"
    r"008dc14922f1584edd6dd670d9773b9d_images_image-e35ff3e6-547a-4462-8ca7-df5cedf4ee7f.png"
)

ROOT = Path(r"D:\CursorProject\ahsteellab-kumashi")
BRAND = ROOT / "app" / "static" / "img" / "brand"
BRAND.mkdir(parents=True, exist_ok=True)

# Keep originals
shutil.copy2(SRC_PRIMARY, BRAND / "kumashi-logo-source.png")
if SRC_KIT.exists():
    shutil.copy2(SRC_KIT, BRAND / "kumashi-brand-kit-reference.png")


def fit_square(img: Image.Image, size: int, bg=(255, 255, 255, 255)) -> Image.Image:
    img = img.convert("RGBA")
    # Trim near-white/gray margins lightly
    canvas = Image.new("RGBA", (size, size), bg)
    # Fit logo inside with padding
    pad = int(size * 0.08)
    max_w = size - pad * 2
    max_h = size - pad * 2
    ratio = min(max_w / img.width, max_h / img.height)
    nw, nh = max(1, int(img.width * ratio)), max(1, int(img.height * ratio))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (size - nw) // 2
    y = (size - nh) // 2
    canvas.paste(resized, (x, y), resized)
    return canvas


def main() -> None:
    primary = Image.open(SRC_PRIMARY)
    # Full logo for login / headers (preserve aspect, white bg)
    login = fit_square(primary, 1024, (255, 255, 255, 255))
    login.save(BRAND / "kumashi-logo.png", "PNG")
    login.convert("RGB").save(BRAND / "kumashi-logo.jpg", "JPEG", quality=92)

    # App icons
    for size, name in [
        (512, "kumashi-icon-512.png"),
        (192, "kumashi-icon-192.png"),
        (180, "apple-touch-icon.png"),
        (48, "kumashi-icon-48.png"),
        (32, "favicon-32x32.png"),
        (16, "favicon-16x16.png"),
    ]:
        fit_square(primary, size).save(BRAND / name, "PNG")

    # Favicon root copy
    fav = ROOT / "app" / "static" / "img" / "favicon.png"
    fit_square(primary, 32).save(fav, "PNG")

    # Dark icon variant (white bg -> invert mark onto navy for sidebar-friendly badge)
    # Keep exact artwork: place original on transparent/white only — do not recolor the mark.
    print("Installed brand files in", BRAND)
    for p in sorted(BRAND.glob("*")):
        print(" ", p.name, p.stat().st_size)


if __name__ == "__main__":
    main()
