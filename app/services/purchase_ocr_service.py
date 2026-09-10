"""Invoice image/PDF text reading via EasyOCR + PaddleOCR (local engines)."""

from __future__ import annotations

import io
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence, Tuple

import numpy as np
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

_easy_lock = threading.Lock()
_paddle_lock = threading.Lock()
_easy_reader = None
_paddle_ocr = None
_easy_error: Optional[str] = None
_paddle_error: Optional[str] = None


@dataclass
class OcrLine:
    text: str
    confidence: float
    engine: str
    y: float = 0.0
    x: float = 0.0
    w: float = 0.0
    h: float = 0.0
    page: int = 0

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y - self.h / 2.0, self.x + self.w, self.y + self.h / 2.0)


@dataclass
class OcrResult:
    text: str
    engines_used: List[str] = field(default_factory=list)
    page_count: int = 0
    warnings: List[str] = field(default_factory=list)
    lines: List[OcrLine] = field(default_factory=list)
    images: List[Any] = field(default_factory=list)


def _import_pil():
    try:
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pillow is required for invoice OCR. Run: pip install pillow",
        ) from exc
    return Image, ImageEnhance, ImageOps


def _bytes_to_images(file_bytes: bytes, mime_type: str) -> List[Any]:
    Image, ImageEnhance, ImageOps = _import_pil()
    mime = (mime_type or "").lower()
    images: List[Any] = []

    if mime == "application/pdf" or file_bytes[:4] == b"%PDF":
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PyMuPDF is required for PDF invoices. Run: pip install pymupdf",
            ) from exc
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            for page in doc:
                # Higher DPI for small print on invoices
                mat = fitz.Matrix(2.5, 2.5)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                images.append(_preprocess(img, ImageEnhance, ImageOps))
        finally:
            doc.close()
    else:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")
        images.append(_preprocess(img, ImageEnhance, ImageOps))

    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read any page/image from the upload.",
        )
    return images


def _preprocess(img, ImageEnhance, ImageOps):
    """Light enhancement for invoice scans (keeps color for stamp/colored text)."""
    # Upscale small images
    w, h = img.size
    if max(w, h) < 1400:
        scale = 1400 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    img = ImageOps.exif_transpose(img)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = ImageEnhance.Sharpness(img).enhance(1.25)
    return img.convert("RGB")


def _get_easyocr():
    global _easy_reader, _easy_error
    if _easy_reader is not None:
        return _easy_reader
    if _easy_error:
        return None
    with _easy_lock:
        if _easy_reader is not None:
            return _easy_reader
        if _easy_error:
            return None
        try:
            import easyocr

            # en + optional urdu/latin digits; GPU off for server stability
            _easy_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            return _easy_reader
        except Exception as exc:  # noqa: BLE001
            _easy_error = str(exc)
            logger.exception("EasyOCR init failed")
            return None


def _get_paddle():
    global _paddle_ocr, _paddle_error
    if _paddle_ocr is not None:
        return _paddle_ocr
    if _paddle_error:
        return None
    with _paddle_lock:
        if _paddle_ocr is not None:
            return _paddle_ocr
        if _paddle_error:
            return None
        try:
            from paddleocr import PaddleOCR

            # PaddleOCR 3.x vs 2.x constructors differ
            init_attempts = [
                dict(
                    lang="en",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                ),
                dict(use_angle_cls=True, lang="en", show_log=False, use_gpu=False),
                dict(use_angle_cls=True, lang="en"),
                dict(lang="en"),
            ]
            last_exc: Exception | None = None
            for kwargs in init_attempts:
                try:
                    _paddle_ocr = PaddleOCR(**kwargs)
                    return _paddle_ocr
                except TypeError as exc:
                    last_exc = exc
                    continue
            if last_exc:
                raise last_exc
            _paddle_ocr = PaddleOCR(lang="en")
            return _paddle_ocr
        except Exception as exc:  # noqa: BLE001
            _paddle_error = str(exc)
            logger.exception("PaddleOCR init failed")
            return None


def _run_easyocr(img) -> List[OcrLine]:
    reader = _get_easyocr()
    if reader is None:
        return []
    arr = np.array(img)
    raw = reader.readtext(arr, detail=1, paragraph=False)
    lines: List[OcrLine] = []
    for item in raw or []:
        try:
            bbox, text, conf = item[0], item[1], float(item[2])
            if not text or not str(text).strip():
                continue
            ys = [p[1] for p in bbox]
            xs = [p[0] for p in bbox]
            x0, x1 = float(min(xs)), float(max(xs))
            y0, y1 = float(min(ys)), float(max(ys))
            lines.append(
                OcrLine(
                    text=str(text).strip(),
                    confidence=conf,
                    engine="easyocr",
                    y=float(sum(ys) / len(ys)),
                    x=x0,
                    w=max(1.0, x1 - x0),
                    h=max(1.0, y1 - y0),
                )
            )
        except (TypeError, ValueError, IndexError):
            continue
    return lines


def _run_paddle(img) -> List[OcrLine]:
    ocr = _get_paddle()
    if ocr is None:
        return []
    arr = np.array(img)
    lines: List[OcrLine] = []
    result = None
    try:
        if hasattr(ocr, "predict"):
            result = ocr.predict(arr)
        else:
            try:
                result = ocr.ocr(arr, cls=True)
            except TypeError:
                result = ocr.ocr(arr)
    except Exception:  # noqa: BLE001
        logger.exception("PaddleOCR page failed")
        return []

    if result is None:
        return []

    # PaddleOCR 3.x predict → list of result objects / dicts
    pages = result if isinstance(result, list) else [result]
    for page in pages:
        data = page
        if hasattr(page, "json") and callable(page.json):
            try:
                data = page.json
            except Exception:  # noqa: BLE001
                data = page
        if hasattr(page, "res") and isinstance(getattr(page, "res"), dict):
            data = page.res
        if isinstance(data, dict):
            # Sometimes nested under 'res'
            if "res" in data and isinstance(data["res"], dict):
                data = data["res"]
            rec_texts = data.get("rec_texts") or data.get("texts") or []
            rec_scores = data.get("rec_scores") or data.get("scores") or []
            rec_boxes = (
                data.get("rec_polys")
                or data.get("dt_polys")
                or data.get("rec_boxes")
                or data.get("boxes")
                or []
            )
            for i, text in enumerate(rec_texts):
                if not text or not str(text).strip():
                    continue
                conf = float(rec_scores[i]) if i < len(rec_scores) else 0.0
                y = 0.0
                x = 0.0
                if i < len(rec_boxes):
                    box = rec_boxes[i]
                    try:
                        # box may be ndarray Nx2 or flat 8 values
                        pts = np.array(box).reshape(-1, 2)
                        ys = pts[:, 1].astype(float)
                        xs = pts[:, 0].astype(float)
                        y = float(ys.mean())
                        x = float(xs.min())
                    except (TypeError, ValueError, IndexError):
                        pass
                w = h = 0.0
                if i < len(rec_boxes):
                    try:
                        pts = np.array(rec_boxes[i]).reshape(-1, 2)
                        w = float(pts[:, 0].max() - pts[:, 0].min())
                        h = float(pts[:, 1].max() - pts[:, 1].min())
                    except (TypeError, ValueError, IndexError):
                        pass
                lines.append(
                    OcrLine(str(text).strip(), conf, "paddleocr", y, x, max(1.0, w), max(1.0, h))
                )
            continue

        # Classic 2.x: [[ [bbox, (text, conf)], ... ]]
        page_lines = data
        if page_lines and isinstance(page_lines, list) and page_lines and isinstance(page_lines[0], list):
            # could be full doc [page] or already page lines
            if page_lines[0] and isinstance(page_lines[0][0], (list, tuple)) and len(page_lines[0]) == 2:
                pass  # already lines
            elif page_lines[0] and isinstance(page_lines[0][0], list):
                page_lines = page_lines[0]
        if not page_lines:
            continue
        for item in page_lines:
            try:
                if not item:
                    continue
                bbox = item[0]
                payload = item[1]
                if isinstance(payload, (list, tuple)):
                    text, conf = payload[0], float(payload[1])
                else:
                    text, conf = str(payload), 0.0
                if not text or not str(text).strip():
                    continue
                ys = [float(p[1]) for p in bbox]
                xs = [float(p[0]) for p in bbox]
                lines.append(
                    OcrLine(
                        text=str(text).strip(),
                        confidence=conf,
                        engine="paddleocr",
                        y=sum(ys) / len(ys),
                        x=min(xs),
                        w=max(1.0, max(xs) - min(xs)),
                        h=max(1.0, max(ys) - min(ys)),
                    )
                )
            except (TypeError, ValueError, IndexError):
                continue
    return lines


def _normalize_key(text: str) -> str:
    return " ".join(text.lower().split())


def _merge_page_lines(easy_lines: Sequence[OcrLine], paddle_lines: Sequence[OcrLine]) -> List[OcrLine]:
    """Merge both engines: keep unique lines, prefer higher confidence / longer text."""
    merged: List[OcrLine] = []
    pool = list(easy_lines) + list(paddle_lines)
    pool.sort(key=lambda ln: (round(ln.y / 8.0), ln.x))

    for ln in pool:
        key = _normalize_key(ln.text)
        if not key:
            continue
        dup = None
        for existing in merged:
            ek = _normalize_key(existing.text)
            same_row = abs(existing.y - ln.y) < 18
            overlap = key in ek or ek in key or key == ek
            if same_row and overlap:
                dup = existing
                break
        if dup is None:
            merged.append(ln)
            continue
        # Prefer higher confidence, then longer text
        if (ln.confidence, len(ln.text)) > (dup.confidence, len(dup.text)):
            merged[merged.index(dup)] = ln
    merged.sort(key=lambda ln: (ln.y, ln.x))
    return merged


def _lines_to_text(lines: Sequence[OcrLine]) -> str:
    if not lines:
        return ""
    # Group into approximate rows
    rows: List[List[OcrLine]] = []
    for ln in lines:
        if not rows:
            rows.append([ln])
            continue
        if abs(rows[-1][0].y - ln.y) < 14:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    out_rows = []
    for row in rows:
        row.sort(key=lambda x: x.x)
        out_rows.append("  ".join(x.text for x in row))
    return "\n".join(out_rows)


class PurchaseOcrService:
    """Local dual-engine OCR for supplier invoices."""

    def read(self, *, file_bytes: bytes, mime_type: str) -> OcrResult:
        images = _bytes_to_images(file_bytes, mime_type)
        all_lines: List[OcrLine] = []
        engines: List[str] = []
        warnings: List[str] = []

        easy = _get_easyocr()
        paddle = _get_paddle()
        if easy is None and paddle is None:
            detail = "Neither EasyOCR nor PaddleOCR could start."
            if _easy_error:
                detail += f" EasyOCR: {_easy_error[:180]}"
            if _paddle_error:
                detail += f" PaddleOCR: {_paddle_error[:180]}"
            detail += " Install with: pip install easyocr paddlepaddle paddleocr pymupdf pillow numpy"
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

        for page_idx, img in enumerate(images, start=1):
            easy_lines = _run_easyocr(img) if easy is not None else []
            paddle_lines = _run_paddle(img) if paddle is not None else []
            for ln in easy_lines + paddle_lines:
                ln.page = page_idx - 1
            if easy_lines and "easyocr" not in engines:
                engines.append("easyocr")
            if paddle_lines and "paddleocr" not in engines:
                engines.append("paddleocr")
            page_merged = _merge_page_lines(easy_lines, paddle_lines)
            for ln in page_merged:
                ln.page = page_idx - 1
            if len(images) > 1:
                all_lines.append(
                    OcrLine(
                        text=f"--- PAGE {page_idx} ---",
                        confidence=1.0,
                        engine="system",
                        y=-1,
                        x=0,
                        page=page_idx - 1,
                    )
                )
            all_lines.extend(page_merged)
            if not page_merged:
                warnings.append(f"Page {page_idx}: OCR returned no text.")

        if _easy_error and "easyocr" not in engines:
            warnings.append(f"EasyOCR unavailable: {_easy_error[:160]}")
        if _paddle_error and "paddleocr" not in engines:
            warnings.append(f"PaddleOCR unavailable: {_paddle_error[:160]}")

        text = _lines_to_text([ln for ln in all_lines if ln.engine != "system"])
        # Keep page markers in full text
        full_parts = []
        buf: List[OcrLine] = []
        for ln in all_lines:
            if ln.engine == "system":
                if buf:
                    full_parts.append(_lines_to_text(buf))
                    buf = []
                full_parts.append(ln.text)
            else:
                buf.append(ln)
        if buf:
            full_parts.append(_lines_to_text(buf))
        text = "\n".join(p for p in full_parts if p).strip()

        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="OCR could not read any text. Try a clearer scan or higher-resolution photo.",
            )

        return OcrResult(
            text=text,
            engines_used=engines,
            page_count=len(images),
            warnings=warnings,
            lines=[ln for ln in all_lines if ln.engine != "system"],
            images=images,
        )
