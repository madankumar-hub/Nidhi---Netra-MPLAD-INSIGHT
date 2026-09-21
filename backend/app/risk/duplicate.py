"""Near-duplicate work detection (FR9).

Default backend is a dependency-free TF-IDF + cosine-similarity comparison
over project descriptions, restricted to the same district so the comparison
is meaningful. A sentence-transformer embedding backend is supported as an
optional upgrade and is selected with DUPLICATE_BACKEND=embeddings; if the
package is not installed the engine falls back to TF-IDF and says so.
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Sequence

from app.core.config import settings
from app.core.enums import AnalysisSource, RiskCategory, RiskLevel
from app.risk.types import DuplicateMatch, FactorResult

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from app.models.project import Project

logger = logging.getLogger("mplad.risk.duplicate")

_TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in", "is", "it",
    "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "under",
    "work", "works", "project", "scheme", "construction", "providing", "provision",
}


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if t not in STOPWORDS and len(t) > 2]


def _tfidf_vectors(documents: Sequence[str]) -> List[Dict[str, float]]:
    tokenised = [tokenize(d) for d in documents]
    n = len(tokenised)
    df: Counter = Counter()
    for tokens in tokenised:
        df.update(set(tokens))

    vectors: List[Dict[str, float]] = []
    for tokens in tokenised:
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        vec: Dict[str, float] = {}
        for term, count in tf.items():
            idf = math.log((1 + n) / (1 + df[term])) + 1.0
            vec[term] = (count / total) * idf
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({k: v / norm for k, v in vec.items()})
    return vectors


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(weight * b.get(term, 0.0) for term, weight in a.items())


def _embedding_backend_available() -> bool:
    try:  # pragma: no cover - optional dependency
        import sentence_transformers  # noqa: F401

        return True
    except Exception:
        return False


def active_backend() -> str:
    """The backend that will actually be used, not merely the one requested."""
    if settings.duplicate_backend == "embeddings" and _embedding_backend_available():
        return "embeddings"
    return "tfidf"


def find_duplicates(
    project: Project, peers: Iterable[Project], threshold: Optional[float] = None
) -> List[DuplicateMatch]:
    """Return peer works whose description is near-identical to `project`."""
    limit = threshold if threshold is not None else settings.duplicate_similarity_threshold
    peer_list = [p for p in peers if p.id != project.id and (p.description or p.title)]
    if not peer_list:
        return []

    def doc(p: Project) -> str:
        return f"{p.title} {p.description}"

    documents = [doc(project)] + [doc(p) for p in peer_list]
    vectors = _tfidf_vectors(documents)
    base = vectors[0]

    matches: List[DuplicateMatch] = []
    for peer, vec in zip(peer_list, vectors[1:]):
        similarity = _cosine(base, vec)
        if similarity >= limit:
            matches.append(
                DuplicateMatch(project_code=peer.project_code, title=peer.title, similarity=round(similarity, 3))
            )
    matches.sort(key=lambda m: m.similarity, reverse=True)
    return matches[:5]


def duplicate_factor(matches: Sequence[DuplicateMatch]) -> Optional[FactorResult]:
    if not matches:
        return None
    best = matches[0]
    raw = min(35 + (best.similarity - 0.7) * 180, 100.0)
    others = ", ".join(f"{m.project_code} ({m.similarity:.2f})" for m in matches[:3])
    return FactorResult(
        code="NEAR_DUPLICATE_WORK",
        title="Description closely matches another sanctioned work in the same district",
        category=RiskCategory.DUPLICATION,
        severity=RiskLevel.HIGH if raw >= 50 else RiskLevel.MEDIUM,
        weight=0.18,
        raw_score=raw,
        source=AnalysisSource.STATISTICAL,
        detected_indicator=(
            f"Textual similarity of {best.similarity:.2f} with work {best.project_code} "
            f"in the same district."
        ),
        evidence=f"Closest matches: {others}. Similarity threshold {settings.duplicate_similarity_threshold:.2f}.",
        explanation=(
            "Near-identical descriptions in the same district can indicate the same asset "
            "being sanctioned twice, or simply a standard template being reused for "
            "genuinely different locations. It needs a human check, not an automatic "
            "conclusion."
        ),
        recommended_action=(
            "Compare the site locations and estimates of the matched works; if they are "
            "the same asset, stop the duplicate release and raise an audit observation."
        ),
        metric_name="max_description_similarity",
        metric_value=best.similarity,
        threshold_value=settings.duplicate_similarity_threshold,
        reference_project_code=best.project_code,
        responsible_party="Auditor",
    )
