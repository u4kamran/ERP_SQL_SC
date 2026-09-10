"""Image download validation and WEBP optimization."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, UnidentifiedImageError

from app.services.item_images import item_image_dir

ALLOWED_MIME = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass
class ValidatedImage:
    content: bytes
    content_hash: str
    width: int
    height: int
    mime_type: str
    primary_path: Path
    thumb_path: Path
    relative_primary: str
    relative_thumb: str


def _sniff_mime(content: bytes, content_type: str | None) -> Optional[str]:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in ALLOWED_MIME:
        return ct
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def download_and_validate(
    image_url: str,
    item_id: float,
    *,
    timeout: float = 15.0,
    min_width: int = 80,
    min_height: int = 80,
    max_bytes: int = 8_000_000,
    filename_stem: str = "primary",
) -> ValidatedImage:
    if not image_url or not image_url.startswith(("http://", "https://")):
        raise ValueError("Invalid image URL")

    headers = {"User-Agent": "AHSteelLabItemImages/1.0", "Accept": "image/*,*/*"}
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
        with client.stream("GET", image_url) as resp:
            if resp.status_code != 200:
                raise ValueError(f"Image URL not accessible ({resp.status_code})")
            chunks: list[bytes] = []
            total = 0
            for chunk in resp.iter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("Image too large")
                chunks.append(chunk)
            content = b"".join(chunks)
            mime = _sniff_mime(content, resp.headers.get("content-type"))

    if not mime:
        raise ValueError("Unsupported or invalid image type")
    if len(content) < 100:
        raise ValueError("Image too small / empty")

    try:
        img = Image.open(io.BytesIO(content))
        img.load()
    except UnidentifiedImageError as exc:
        raise ValueError("Corrupted or unreadable image") from exc

    width, height = img.size
    if width < min_width or height < min_height:
        raise ValueError(f"Image resolution too small ({width}x{height})")

    # Convert to WEBP primary + thumbnail
    folder = item_image_dir(item_id)
    primary = folder / f"{filename_stem}.webp"
    thumb = folder / f"{filename_stem}_thumb.webp"

    rgb = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
    if rgb.mode == "RGBA":
        background = Image.new("RGB", rgb.size, (255, 255, 255))
        background.paste(rgb, mask=rgb.split()[-1])
        rgb = background
    else:
        rgb = rgb.convert("RGB")

    max_side = 1200
    if max(rgb.size) > max_side:
        rgb.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    rgb.save(primary, format="WEBP", quality=82, method=4)

    thumb_img = rgb.copy()
    thumb_img.thumbnail((240, 240), Image.Resampling.LANCZOS)
    thumb_img.save(thumb, format="WEBP", quality=75, method=4)

    digest = hashlib.sha256(primary.read_bytes()).hexdigest()
    # Relative paths stored from project root data/
    rel_primary = f"ProductImages/{primary.parent.name}/{primary.name}"
    rel_thumb = f"ProductImages/{thumb.parent.name}/{thumb.name}"

    return ValidatedImage(
        content=primary.read_bytes(),
        content_hash=digest,
        width=rgb.size[0],
        height=rgb.size[1],
        mime_type="image/webp",
        primary_path=primary,
        thumb_path=thumb,
        relative_primary=rel_primary,
        relative_thumb=rel_thumb,
    )


def validate_upload_bytes(
    content: bytes,
    item_id: float,
    *,
    min_width: int = 80,
    min_height: int = 80,
    max_bytes: int = 8_000_000,
    filename_stem: str = "manual",
) -> ValidatedImage:
    if len(content) > max_bytes:
        raise ValueError("Upload too large")
    mime = _sniff_mime(content, None)
    if not mime:
        raise ValueError("Only JPG, PNG, or WEBP uploads are allowed")
    # Reuse download path by wrapping as in-memory "validated" via same Pillow path
    # Write temp then process similarly
    try:
        img = Image.open(io.BytesIO(content))
        img.load()
    except UnidentifiedImageError as exc:
        raise ValueError("Corrupted or unreadable image") from exc

    width, height = img.size
    if width < min_width or height < min_height:
        raise ValueError(f"Image resolution too small ({width}x{height})")

    folder = item_image_dir(item_id)
    primary = folder / f"{filename_stem}.webp"
    thumb = folder / f"{filename_stem}_thumb.webp"
    rgb = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
    if rgb.mode == "RGBA":
        background = Image.new("RGB", rgb.size, (255, 255, 255))
        background.paste(rgb, mask=rgb.split()[-1])
        rgb = background
    else:
        rgb = rgb.convert("RGB")
    max_side = 1200
    if max(rgb.size) > max_side:
        rgb.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    rgb.save(primary, format="WEBP", quality=82, method=4)
    thumb_img = rgb.copy()
    thumb_img.thumbnail((240, 240), Image.Resampling.LANCZOS)
    thumb_img.save(thumb, format="WEBP", quality=75, method=4)
    digest = hashlib.sha256(primary.read_bytes()).hexdigest()
    return ValidatedImage(
        content=primary.read_bytes(),
        content_hash=digest,
        width=rgb.size[0],
        height=rgb.size[1],
        mime_type="image/webp",
        primary_path=primary,
        thumb_path=thumb,
        relative_primary=f"ProductImages/{primary.parent.name}/{primary.name}",
        relative_thumb=f"ProductImages/{thumb.parent.name}/{thumb.name}",
    )
