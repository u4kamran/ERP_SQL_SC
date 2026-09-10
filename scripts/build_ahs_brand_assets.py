"""Build AHS STEEL web/favicon assets from the approved brand-sheet crop (ARP only)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ARP_BRAND = Path(r"D:\CursorProject\ahsteellab-arp\app\static\img\brand")
LOCKUP_SRC = ARP_BRAND / "try2-lockup.png"


def _trim(im: Image.Image, pad: int = 12) -> Image.Image:
    bg = im.convert("RGB")
    # Trim near-white margins
    w, h = bg.size
    px = bg.load()
    def is_bg(x, y):
        r, g, b = px[x, y]
        return r > 232 and g > 232 and b > 232

    left, top, right, bottom = 0, 0, w - 1, h - 1
    while left < right and all(is_bg(left, y) for y in range(h)):
        left += 1
    while right > left and all(is_bg(right, y) for y in range(h)):
        right -= 1
    while top < bottom and all(is_bg(x, top) for x in range(w)):
        top += 1
    while bottom > top and all(is_bg(x, bottom) for x in range(w)):
        bottom -= 1
    box = (
        max(0, left - pad),
        max(0, top - pad),
        min(w, right + 1 + pad),
        min(h, bottom + 1 + pad),
    )
    return im.crop(box)


def _fit_square(im: Image.Image, size: int, radius: int | None = None) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    src = im.convert("RGBA")
    src.thumbnail((int(size * 0.82), int(size * 0.82)), Image.Resampling.LANCZOS)
    x = (size - src.width) // 2
    y = (size - src.height) // 2
    canvas.paste(src, (x, y), src)
    if radius:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(canvas, (0, 0))
        out.putalpha(mask)
        return out
    return canvas


def main() -> None:
    ARP_BRAND.mkdir(parents=True, exist_ok=True)
    lockup = _trim(Image.open(LOCKUP_SRC).convert("RGBA"), pad=16)
    lockup.save(ARP_BRAND / "ahs-logo.png", optimize=True)
    # Wordmark lockup for print (high-res)
    print_w = 1600
    ratio = print_w / lockup.width
    print_img = lockup.resize((print_w, int(lockup.height * ratio)), Image.Resampling.LANCZOS)
    print_img.save(ARP_BRAND / "ahs-logo-print.png", optimize=True)

    # Geometric mark = upper portion of lockup (exclude wordmark/tagline)
    mark = lockup.crop((0, 0, lockup.width, int(lockup.height * 0.52)))
    mark = _trim(mark, pad=8)
    mark.save(ARP_BRAND / "ahs-mark.png", optimize=True)

    sizes = (16, 32, 48, 64, 180, 192, 512)
    for size in sizes:
        radius = max(3, size // 6)
        icon = _fit_square(mark, size, radius=radius)
        icon.save(ARP_BRAND / f"ahs-icon-{size}.png", optimize=True)

    # Apple / PWA aliases
    Image.open(ARP_BRAND / "ahs-icon-180.png").save(ARP_BRAND / "apple-touch-icon.png")
    Image.open(ARP_BRAND / "ahs-icon-192.png").save(ARP_BRAND / "android-chrome-192x192.png")
    Image.open(ARP_BRAND / "ahs-icon-512.png").save(ARP_BRAND / "android-chrome-512x512.png")
    Image.open(ARP_BRAND / "ahs-icon-32.png").save(ARP_BRAND / "favicon-32x32.png")
    Image.open(ARP_BRAND / "ahs-icon-16.png").save(ARP_BRAND / "favicon-16x16.png")
    print("AHS brand assets written to", ARP_BRAND)


if __name__ == "__main__":
    main()
