from dataclasses import dataclass

from equitylens.metrics import (
    get_metric_definition,
)


@dataclass(frozen=True)
class EvidenceQueryDefinition:
    metric_id: str
    query: str


EVIDENCE_QUERY_DEFINITIONS = (
    EvidenceQueryDefinition(
        metric_id="net_operating_income",
        query=(
            "What drove net operating income?"
        ),
    ),
    EvidenceQueryDefinition(
        metric_id="adjusted_operating_income",
        query=(
            "What drove adjusted operating income?"
        ),
    ),
    EvidenceQueryDefinition(
        metric_id="operating_cash_flow",
        query="What drove cash flow?",
    ),
    EvidenceQueryDefinition(
        metric_id="total_equity_production",
        query="What drove production?",
    ),
    EvidenceQueryDefinition(
        metric_id=(
            "renewable_power_generation"
        ),
        query=(
            "What drove renewable power generation?"
        ),
    ),
)


EVIDENCE_QUERY_REGISTRY = {
    definition.metric_id: definition
    for definition
    in EVIDENCE_QUERY_DEFINITIONS
}


def get_evidence_query(
    metric_id: str,
) -> str | None:
    """
    Return the validated narrative-evidence query
    for a registered financial metric.

    A valid financial metric may intentionally return
    None when no narrative query has been validated yet.
    """

    get_metric_definition(
        metric_id
    )

    definition = (
        EVIDENCE_QUERY_REGISTRY.get(
            metric_id
        )
    )

    if definition is None:
        return None

    return definition.query


def get_evidence_enabled_metric_ids(
) -> tuple[str, ...]:
    return tuple(
        definition.metric_id
        for definition
        in EVIDENCE_QUERY_DEFINITIONS
    )