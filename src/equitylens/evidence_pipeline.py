from collections.abc import Iterable

from equitylens.evidence_assessment import (
    EvidenceAssessment,
    assess_retrieved_evidence,
)
from equitylens.evidence_queries import (
    get_evidence_query,
)
from equitylens.evidence_retrieval import (
    DEFAULT_CANDIDATE_K,
    NarrativeEvidenceRetriever,
)
from equitylens.financial_dataset import (
    MultiPeriodFinancialDataset,
)
from equitylens.metrics import (
    get_metric_definition,
)
from equitylens.parser import ParsedPage
from equitylens.text_chunks import chunk_pages

DEFAULT_EVIDENCE_TOP_K = 60


def build_evidence_assessments(
    document_id: str,
    pages: Iterable[ParsedPage],
    dataset: MultiPeriodFinancialDataset,
    metric_ids: tuple[str, ...],
    from_period: str,
    to_period: str,
    top_k: int = DEFAULT_EVIDENCE_TOP_K,
    candidate_k: int = DEFAULT_CANDIDATE_K,
) -> dict[str, EvidenceAssessment]:
    """
    Build narrative evidence assessments for metrics
    with validated evidence queries.

    FinancialChange remains the source of truth for
    the comparison basis. Metric definitions provide
    the analytical scope used to guard evidence
    eligibility.

    Metrics without a validated evidence query are
    intentionally skipped.
    """

    if not document_id.strip():
        raise ValueError(
            "document_id cannot be empty."
        )

    if not metric_ids:
        raise ValueError(
            "metric_ids cannot be empty."
        )

    if len(metric_ids) != len(
        set(metric_ids)
    ):
        raise ValueError(
            "metric_ids must be unique."
        )

    materialized_pages = tuple(
        pages
    )

    for page in materialized_pages:
        if (
            page.document_id
            != document_id
        ):
            raise ValueError(
                "Parsed page document_id does not "
                "match the requested document."
            )

    chunks = chunk_pages(
        list(materialized_pages)
    )

    retriever = (
        NarrativeEvidenceRetriever(
            chunks
        )
    )

    assessments: dict[
        str,
        EvidenceAssessment,
    ] = {}

    for metric_id in metric_ids:
        query = get_evidence_query(
            metric_id
        )

        if query is None:
            continue

        metric_definition = (
            get_metric_definition(
                metric_id
            )
        )

        change = dataset.compare(
            metric_id=metric_id,
            from_period=from_period,
            to_period=to_period,
        )

        retrieved = retriever.retrieve(
            query=query,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        assessments[
            metric_id
        ] = assess_retrieved_evidence(
            query=query,
            expected_comparison_type=(
                change.comparison_type
            ),
            results=retrieved,
            metric_scope=(
                metric_definition.scope
            ),
        )

    return assessments