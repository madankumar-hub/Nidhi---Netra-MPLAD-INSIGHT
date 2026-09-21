"""Unsupervised machine-learning layer: Isolation Forest anomaly detection.

**Why unsupervised.** The hackathon dataset is synthetic (SRS 2.4), so any
*supervised* classifier would be trained on labels this project generates
itself - it would learn the generator and its reported accuracy would measure
nothing. An isolation forest needs no labels at all. It learns the shape of the
normal population directly from whatever records are in the database, real or
synthetic, and flags the records that sit apart from it. Point it at real MPLADS
data and it retrains on that population with no code change.

**What it adds over the rules.** A threshold rule can only ask one question at a
time: "is utilisation more than 20 points ahead of progress?". The forest works
on an 11-dimensional feature vector, so it catches records where every
individual number is inside its own acceptable band but the *combination* is
unlike anything else in the cohort - a large sanction, on a short duration, with
high utilisation, low beneficiary count and a stale progress return. Those are
precisely the records a rule set never sees.

**How it explains itself.** A raw anomaly score is not actionable, so alongside
the score the layer reports which features drove it: the per-feature robust
z-score against the cohort median, ranked. The officer is told the score, the
percentile, and the three measurements that put the record there.

Implementation is dependency-free (Liu, Ting & Zhou, 2008), so `pip install`
never needs a compiler and the layer always runs. If scikit-learn happens to be
installed the same interface can be backed by its implementation.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple

from app.core.enums import AnalysisSource, RiskCategory, RiskLevel
from app.risk.metrics import compute_metrics
from app.risk.types import FactorResult

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from app.models.project import Project

MODEL_VERSION = "isolation-forest-1.0"

#: The feature vector. Order is fixed - it is part of the model contract.
FEATURE_NAMES: Tuple[str, ...] = (
    "allocated_amount",
    "utilization_percent",
    "progress_percent",
    "schedule_variance",
    "utilization_progress_gap",
    "time_elapsed_percent",
    "duration_days",
    "days_since_progress_update",
    "cost_overrun_percent",
    "cost_per_beneficiary",
    "expenditure_entries",
)

#: Human-readable labels for the explanation text.
FEATURE_LABELS: Dict[str, str] = {
    "allocated_amount": "sanctioned amount",
    "utilization_percent": "fund utilisation",
    "progress_percent": "physical progress",
    "schedule_variance": "progress against the planned schedule",
    "utilization_progress_gap": "gap between spending and progress",
    "time_elapsed_percent": "share of the project window elapsed",
    "duration_days": "sanctioned duration",
    "days_since_progress_update": "days since the last progress return",
    "cost_overrun_percent": "expenditure against the estimate",
    "cost_per_beneficiary": "cost per beneficiary",
    "expenditure_entries": "number of expenditure entries filed",
}

#: Standard isolation-forest hyper-parameters (Liu et al., 2008).
N_TREES = 100
SUBSAMPLE_SIZE = 256
MIN_COHORT = 40

#: Share of the population expected to be anomalous - scikit-learn calls this
#: `contamination`. Flagging by percentile rather than by a fixed score is what
#: keeps the layer useful across datasets: an absolute cut-off that is sensible
#: on a tightly clustered population flags nothing on a diffuse one, and
#: everything on a very tight one. 3% of a 5,000-record scheme is ~150 works,
#: which is a realistic review queue.
CONTAMINATION = 0.03
FLAG_PERCENTILE = (1.0 - CONTAMINATION) * 100.0

#: Absolute floor. Percentile alone would always flag the top 3% even when the
#: population has no genuine outliers, so a record must also be isolated faster
#: than the population average (0.5 by construction) by a clear margin.
FLAG_THRESHOLD = 0.55


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------
def extract_features(project: "Project") -> List[float]:
    """Turn one project record into the fixed-order numeric vector."""
    m = compute_metrics(project)
    beneficiaries = float(getattr(project, "beneficiaries", 0) or 0)
    allocated = float(getattr(project, "allocated_amount", 0) or 0)
    return [
        allocated,
        m.utilization_percent,
        m.progress_percent,
        m.schedule_variance if m.schedule_variance is not None else 0.0,
        m.utilization_progress_gap if m.utilization_progress_gap is not None else 0.0,
        m.time_elapsed_percent if m.time_elapsed_percent is not None else 0.0,
        float(m.duration_days or 0),
        float(m.days_since_progress_update or 0),
        m.cost_overrun_percent if m.cost_overrun_percent is not None else 0.0,
        (allocated / beneficiaries) if beneficiaries > 0 else 0.0,
        float(len(getattr(project, "fund_updates", []) or [])),
    ]


# ---------------------------------------------------------------------------
# Isolation tree
# ---------------------------------------------------------------------------
@dataclass
class _Node:
    """An internal split, or a leaf carrying the size of the region."""

    feature: int = -1
    threshold: float = 0.0
    left: Optional["_Node"] = None
    right: Optional["_Node"] = None
    size: int = 0

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


def _average_path_length(n: int) -> float:
    """Expected path length of an unsuccessful BST search over n points.

    This is the normalising constant c(n) from the original paper.
    """
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    euler_mascheroni = 0.5772156649
    return 2.0 * (math.log(n - 1) + euler_mascheroni) - (2.0 * (n - 1) / n)


def _build_tree(rows: List[List[float]], depth: int, max_depth: int, rng: random.Random) -> _Node:
    if depth >= max_depth or len(rows) <= 1:
        return _Node(size=len(rows))

    n_features = len(rows[0])
    # Try a few features before giving up: a constant column cannot be split.
    for _ in range(min(n_features, 8)):
        feature = rng.randrange(n_features)
        values = [row[feature] for row in rows]
        low, high = min(values), max(values)
        if high - low > 1e-12:
            threshold = rng.uniform(low, high)
            left = [row for row in rows if row[feature] < threshold]
            right = [row for row in rows if row[feature] >= threshold]
            if left and right:
                return _Node(
                    feature=feature,
                    threshold=threshold,
                    left=_build_tree(left, depth + 1, max_depth, rng),
                    right=_build_tree(right, depth + 1, max_depth, rng),
                )
    return _Node(size=len(rows))


def _path_length(node: _Node, row: List[float], depth: int = 0) -> float:
    if node.is_leaf:
        # Points that land in a leaf holding several records are credited with
        # the expected depth of the sub-tree that was never grown.
        return depth + _average_path_length(node.size)
    if row[node.feature] < node.threshold:
        return _path_length(node.left, row, depth + 1)  # type: ignore[arg-type]
    return _path_length(node.right, row, depth + 1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------
@dataclass
class IsolationForestModel:
    """A fitted forest plus the cohort statistics used for explanation."""

    trees: List[_Node] = field(default_factory=list)
    normaliser: float = 1.0
    sample_size: int = 0
    n_trees: int = 0
    feature_median: List[float] = field(default_factory=list)
    feature_mad: List[float] = field(default_factory=list)
    #: Scores of the training population, sorted - used for percentile ranking.
    training_scores: List[float] = field(default_factory=list)
    version: str = MODEL_VERSION

    @property
    def is_fitted(self) -> bool:
        return bool(self.trees)

    # -- scoring ----------------------------------------------------------
    def anomaly_score(self, features: Sequence[float]) -> float:
        """0..1. Above ~0.6 means "isolated quickly, i.e. unlike the rest"."""
        if not self.trees:
            return 0.0
        row = list(features)
        mean_path = sum(_path_length(tree, row) for tree in self.trees) / len(self.trees)
        if self.normaliser <= 0:
            return 0.0
        return round(2.0 ** (-mean_path / self.normaliser), 4)

    def percentile(self, score: float) -> float:
        """Where this score sits in the training population, 0-100."""
        if not self.training_scores:
            return 0.0
        below = sum(1 for value in self.training_scores if value <= score)
        return round(below / len(self.training_scores) * 100.0, 1)

    def feature_deviations(self, features: Sequence[float]) -> List[Tuple[str, float, float, float]]:
        """Ranked (feature, value, cohort median, robust z-score).

        Uses the median and median absolute deviation rather than the mean and
        standard deviation, so one extreme record cannot hide the others.
        """
        out: List[Tuple[str, float, float, float]] = []
        for index, name in enumerate(FEATURE_NAMES):
            if index >= len(features) or index >= len(self.feature_median):
                break
            value = float(features[index])
            median = self.feature_median[index]
            mad = self.feature_mad[index]
            if mad <= 1e-9:
                z = 0.0
            else:
                # 0.6745 converts MAD to a standard-deviation equivalent.
                z = 0.6745 * (value - median) / mad
            out.append((name, value, median, round(z, 2)))
        out.sort(key=lambda item: abs(item[3]), reverse=True)
        return out


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def fit(projects: Sequence["Project"], *, seed: int = 20260101) -> Optional[IsolationForestModel]:
    """Train on the whole cohort. Returns None when there is too little data."""
    rows = [extract_features(project) for project in projects]
    return fit_from_features(rows, seed=seed)


def fit_from_features(
    rows: Sequence[Sequence[float]], *, seed: int = 20260101
) -> Optional[IsolationForestModel]:
    data = [list(row) for row in rows]
    if len(data) < MIN_COHORT:
        return None

    rng = random.Random(seed)
    sample_size = min(SUBSAMPLE_SIZE, len(data))
    max_depth = max(int(math.ceil(math.log2(sample_size))), 1)

    trees: List[_Node] = []
    for _ in range(N_TREES):
        subsample = rng.sample(data, sample_size)
        trees.append(_build_tree(subsample, 0, max_depth, rng))

    n_features = len(data[0])
    medians: List[float] = []
    mads: List[float] = []
    for index in range(n_features):
        column = [row[index] for row in data]
        median = _median(column)
        medians.append(median)
        mads.append(_median([abs(value - median) for value in column]))

    model = IsolationForestModel(
        trees=trees,
        normaliser=_average_path_length(sample_size),
        sample_size=sample_size,
        n_trees=N_TREES,
        feature_median=medians,
        feature_mad=mads,
    )
    model.training_scores = sorted(model.anomaly_score(row) for row in data)
    return model


# ---------------------------------------------------------------------------
# Turning a score into an explainable finding
# ---------------------------------------------------------------------------
def _severity(score: float, percentile: float) -> RiskLevel:
    """Severity comes from how far into the tail the record sits."""
    if percentile >= 99.5 and score >= 0.68:
        return RiskLevel.CRITICAL
    if percentile >= 99.0:
        return RiskLevel.HIGH
    if percentile >= FLAG_PERCENTILE:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _format_value(name: str, value: float) -> str:
    if name in {"allocated_amount"}:
        return f"Rs {value:,.2f} lakh"
    if name in {"cost_per_beneficiary"}:
        return f"Rs {value:,.4f} lakh per beneficiary"
    if name in {"duration_days", "days_since_progress_update"}:
        return f"{value:,.0f} days"
    if name in {"expenditure_entries"}:
        return f"{value:,.0f}"
    return f"{value:,.1f}%"


def evaluate_anomaly(
    project: "Project", model: Optional[IsolationForestModel]
) -> Optional[FactorResult]:
    """Returns a finding only when this record is a genuine multivariate outlier."""
    if model is None or not model.is_fitted:
        return None

    features = extract_features(project)
    score = model.anomaly_score(features)
    percentile = model.percentile(score)
    # Both gates must hold: in the tail of this population, AND isolated
    # meaningfully faster than average in absolute terms.
    if percentile < FLAG_PERCENTILE or score < FLAG_THRESHOLD:
        return None
    deviations = [item for item in model.feature_deviations(features) if abs(item[3]) >= 1.0][:3]
    if not deviations:
        return None

    drivers = ", ".join(
        f"{FEATURE_LABELS.get(name, name)} {_format_value(name, value)} "
        f"(cohort median {_format_value(name, median)}, {z:+.1f} sigma)"
        for name, value, median, z in deviations
    )
    top_label = FEATURE_LABELS.get(deviations[0][0], deviations[0][0])

    # Scale within the tail: at the flag percentile this contributes modestly,
    # at the very top of the population it contributes fully.
    tail_position = (percentile - FLAG_PERCENTILE) / max(100.0 - FLAG_PERCENTILE, 0.1)
    raw = min(35.0 + tail_position * 65.0, 100.0)

    return FactorResult(
        code="ML_MULTIVARIATE_ANOMALY",
        title="Record is a statistical outlier across several measures at once",
        category=RiskCategory.IMPLEMENTATION,
        severity=_severity(score, percentile),
        weight=0.16,
        raw_score=raw,
        source=AnalysisSource.MACHINE_LEARNING,
        detected_indicator=(
            f"An isolation forest trained on {len(model.training_scores):,} comparable works "
            f"scores this record {score:.2f}, placing it in the "
            f"{percentile:.0f}th percentile of unusualness. The strongest driver is "
            f"{top_label}."
        ),
        evidence=f"Features furthest from the cohort: {drivers}.",
        explanation=(
            "No single threshold has been breached here - each figure on its own sits "
            "inside its normal band. What the model has found is that this combination "
            "of figures does not occur elsewhere in the dataset. Unusual is not the same "
            "as wrong, so this is a prompt to look, not a conclusion."
        ),
        recommended_action=(
            "Review the record alongside comparable works in the same category and "
            "district, and confirm that the combination above reflects the actual scope."
        ),
        metric_name="isolation_forest_score",
        metric_value=score,
        threshold_value=FLAG_THRESHOLD,
        responsible_party="Auditor",
    )


def describe(model: Optional[IsolationForestModel]) -> dict:
    return {
        "available": bool(model and model.is_fitted),
        "model": MODEL_VERSION,
        "algorithm": "Isolation Forest (unsupervised, Liu/Ting/Zhou 2008)",
        "trees": model.n_trees if model else 0,
        "subsample_size": model.sample_size if model else 0,
        "features": len(FEATURE_NAMES),
        "feature_names": list(FEATURE_NAMES),
        "trained_on_records": len(model.training_scores) if model else 0,
        "flag_threshold": FLAG_THRESHOLD,
        "flag_percentile": FLAG_PERCENTILE,
        "contamination": CONTAMINATION,
        "minimum_cohort": MIN_COHORT,
        "supervised": False,
        "notes": (
            "Unsupervised: the model is fitted on the live project population and needs "
            f"no labels, so it transfers to real MPLADS data without retraining on "
            f"hand-made examples. It flags roughly the most unusual "
            f"{CONTAMINATION * 100:.0f}% of records, contributes one explainable factor "
            "to the overall score, and never sets the risk level on its own."
        ),
    }
