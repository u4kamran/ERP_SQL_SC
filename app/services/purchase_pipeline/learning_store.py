"""Supplier-specific learning store (aliases, handwritten IDs, extraction rules).

JSON file under data/purchase_pipeline — independently replaceable with a DB backend.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.settings import _PROJECT_ROOT

logger = logging.getLogger(__name__)

DEFAULT_PATH = _PROJECT_ROOT / "data" / "purchase_pipeline" / "learning.json"


class LearningStore:
    """Persist corrections so later invoices improve matching."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {"suppliers": {}, "global_aliases": {}}
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
                self._data.setdefault("suppliers", {})
                self._data.setdefault("global_aliases", {})
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load learning store; starting empty")
            self._data = {"suppliers": {}, "global_aliases": {}}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    def _supplier_bucket(self, supplier_key: str) -> Dict[str, Any]:
        suppliers = self._data.setdefault("suppliers", {})
        if supplier_key not in suppliers:
            suppliers[supplier_key] = {
                "aliases": {},  # alias text -> item_id
                "manual_id_map": {},  # handwritten text -> item_id
                "supplier_codes": {},  # printed product code -> item_id
                "extraction_rules": {},
            }
        return suppliers[supplier_key]

    def lookup_alias(self, *, supplier_key: str, text: str) -> Optional[float]:
        key = _norm(text)
        if not key:
            return None
        bucket = self._supplier_bucket(supplier_key)
        for store in (bucket.get("aliases", {}), self._data.get("global_aliases", {})):
            if key in store:
                try:
                    return float(store[key])
                except (TypeError, ValueError):
                    return None
        return None

    def lookup_manual_id(self, *, supplier_key: str, handwritten: str) -> Optional[float]:
        key = _norm(handwritten)
        if not key:
            return None
        mapped = self._supplier_bucket(supplier_key).get("manual_id_map", {}).get(key)
        try:
            return float(mapped) if mapped is not None else None
        except (TypeError, ValueError):
            return None

    def lookup_supplier_code(self, *, supplier_key: str, code: str) -> Optional[float]:
        key = _norm(code)
        if not key:
            return None
        mapped = self._supplier_bucket(supplier_key).get("supplier_codes", {}).get(key)
        try:
            return float(mapped) if mapped is not None else None
        except (TypeError, ValueError):
            return None

    def get_extraction_rules(self, supplier_key: str) -> Dict[str, Any]:
        return dict(self._supplier_bucket(supplier_key).get("extraction_rules") or {})

    def get_fetch_instructions(self) -> str:
        return str(self._data.get("fetch_instructions") or "")

    def set_fetch_instructions(self, text: str) -> str:
        cleaned = str(text or "").strip()
        with self._lock:
            self._data["fetch_instructions"] = cleaned
            self._save()
        return cleaned

    def record_correction(
        self,
        *,
        supplier_key: str,
        item_id: float,
        alias: str = "",
        handwritten_manual_id: str = "",
        supplier_product_code: str = "",
        extraction_rule: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Stage 13 — learn from user corrections. Returns list of applied update labels."""
        applied: List[str] = []
        with self._lock:
            bucket = self._supplier_bucket(supplier_key)
            if alias and _norm(alias):
                bucket["aliases"][_norm(alias)] = float(item_id)
                applied.append(f"alias:{_norm(alias)}→{item_id}")
            if handwritten_manual_id and _norm(handwritten_manual_id):
                bucket["manual_id_map"][_norm(handwritten_manual_id)] = float(item_id)
                applied.append(f"hw_manual:{_norm(handwritten_manual_id)}→{item_id}")
            if supplier_product_code and _norm(supplier_product_code):
                bucket["supplier_codes"][_norm(supplier_product_code)] = float(item_id)
                applied.append(f"supplier_code:{_norm(supplier_product_code)}→{item_id}")
            if extraction_rule:
                rules = bucket.setdefault("extraction_rules", {})
                rules.update(extraction_rule)
                applied.append("extraction_rule")
            if applied:
                self._save()
        return applied


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().split())
