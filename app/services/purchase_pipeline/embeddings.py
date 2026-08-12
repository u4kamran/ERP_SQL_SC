"""Lightweight text similarity / embedding interface (replaceable)."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple


_TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


def jaccard(a: str, b: str) -> float:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def fuzzy_ratio(a: str, b: str) -> float:
    """Token-sort + character bigram Dice — no external fuzzy lib required."""
    sa = " ".join(sorted(tokenize(a)))
    sb = " ".join(sorted(tokenize(b)))
    if not sa or not sb:
        return 0.0
    if sa == sb:
        return 1.0
    ba = Counter(sa[i : i + 2] for i in range(max(0, len(sa) - 1)))
    bb = Counter(sb[i : i + 2] for i in range(max(0, len(sb) - 1)))
    if not ba or not bb:
        return jaccard(a, b)
    inter = sum((ba & bb).values())
    return (2.0 * inter) / (sum(ba.values()) + sum(bb.values()))


def _tfidf_vector(tokens: Sequence[str], idf: Dict[str, float]) -> Dict[str, float]:
    tf = Counter(tokens)
    n = max(1, len(tokens))
    return {t: (c / n) * idf.get(t, 1.0) for t, c in tf.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


class SemanticEmbedder:
    """
    Stage 9 semantic embeddings — default TF-IDF cosine.
    Swap this class for sentence-transformers without changing the match stage.
    """

    def __init__(self, corpus: Iterable[str] | None = None):
        self._idf: Dict[str, float] = {}
        docs = list(corpus or [])
        if docs:
            self.fit(docs)

    def fit(self, documents: Sequence[str]) -> None:
        df: Counter = Counter()
        for doc in documents:
            for t in set(tokenize(doc)):
                df[t] += 1
        n = max(1, len(documents))
        self._idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

    def similarity(self, a: str, b: str) -> float:
        va = _tfidf_vector(tokenize(a), self._idf)
        vb = _tfidf_vector(tokenize(b), self._idf)
        return _cosine(va, vb)

    def best_match(
        self, query: str, candidates: Sequence[Tuple[str, float]], *, min_score: float = 0.35
    ) -> Tuple[int, float]:
        """candidates is list of (text, item_id). Returns (index, score) or (-1, 0)."""
        best_i, best_s = -1, 0.0
        for i, (text, _iid) in enumerate(candidates):
            s = self.similarity(query, text)
            if s > best_s:
                best_i, best_s = i, s
        if best_s < min_score:
            return -1, 0.0
        return best_i, best_s
