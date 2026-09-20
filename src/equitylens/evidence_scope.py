from typing import Literal

from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
    EQUINOR_Q1_2026,
    EQUINOR_Q2_2026,
)
from equitylens.metrics import MetricScope

EvidenceScope = Literal[
    "group",
    "segment",
    "asset",
    "unknown",
]

ScopeCompatibility = Literal[
    "compatible",
    "mismatched",
    "unknown",
]


_AKER_BP_DOCUMENT_IDS = {
    AKER_BP_Q1_2026.document_id,
    AKER_BP_Q2_2026.document_id,
}

_EQUINOR_DOCUMENT_IDS = {
    EQUINOR_Q1_2026.document_id,
    EQUINOR_Q2_2026.document_id,
}


_AKER_BP_ASSET_SECTION_MARKERS = (
    "alvheim area",
    "eiga area",
    "johan sverdrup",
    "skarv area",
    "ula area",
    "valhall area",
)


_AKER_BP_GROUP_SECTION_MARKERS = (
    "first quarter 2026 results",
    "second quarter 2026 results",
    "key figures",
    "cash flow",
    "outlook",
)


_EQUINOR_GROUP_SECTION_PREFIXES = (
    "equinor first quarter 2026 results",
    "equinor second quarter 2026 results",
    "group review",
)


_EQUINOR_SEGMENT_SECTION_PREFIXES = (
    "exploration & production norway",
    "exploration & production international",
    "exploration & production usa",
    "marketing, midstream & processing",
    "power ",
)


def _normalize_text(
    text: str,
) -> str:
    return " ".join(
        text.lower().split()
    )


def _resolve_aker_bp_scope(
    section_context: str,
) -> EvidenceScope:
    normalized = _normalize_text(
        section_context
    )

    if any(
        marker in normalized
        for marker
        in _AKER_BP_ASSET_SECTION_MARKERS
    ):
        return "asset"

    if any(
        marker in normalized
        for marker
        in _AKER_BP_GROUP_SECTION_MARKERS
    ):
        return "group"

    return "unknown"


def _resolve_equinor_scope(
    section_context: str,
) -> EvidenceScope:
    normalized = _normalize_text(
        section_context
    )

    if any(
        normalized.startswith(prefix)
        for prefix
        in _EQUINOR_SEGMENT_SECTION_PREFIXES
    ):
        return "segment"

    if any(
        normalized.startswith(prefix)
        for prefix
        in _EQUINOR_GROUP_SECTION_PREFIXES
    ):
        return "group"

    return "unknown"


def resolve_evidence_scope(
    document_id: str,
    section_context: str,
) -> EvidenceScope:
    """
    Resolve the analytical scope of narrative evidence.

    Scope resolution is deliberately conservative and
    document-profile aware. Unknown structures remain
    unknown rather than being assumed to represent
    group-level evidence.
    """

    if not document_id.strip():
        raise ValueError(
            "document_id cannot be empty."
        )

    if document_id in _AKER_BP_DOCUMENT_IDS:
        return _resolve_aker_bp_scope(
            section_context
        )

    if document_id in _EQUINOR_DOCUMENT_IDS:
        return _resolve_equinor_scope(
            section_context
        )

    return "unknown"


def assess_scope_compatibility(
    metric_scope: MetricScope,
    evidence_scope: EvidenceScope,
) -> ScopeCompatibility:
    """
    Determine whether evidence scope is sufficiently aligned
    with the analytical scope of a metric.

    Group-level metrics may only treat explicitly group-level
    evidence as compatible. Segment- or asset-level evidence
    cannot independently explain a consolidated group metric.

    Non-group scopes remain unresolved until scope identity,
    such as a specific segment or asset, is modelled explicitly.
    """

    if (
        metric_scope == "unknown"
        or evidence_scope == "unknown"
    ):
        return "unknown"

    if metric_scope == "group":
        if evidence_scope == "group":
            return "compatible"

        return "mismatched"

    return "unknown"