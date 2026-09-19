from dataclasses import dataclass

from equitylens.analysis_pipeline import (
    PeriodSource,
    build_multi_period_financial_dataset,
)
from equitylens.analyst_report import (
    AnalystReport,
    build_analyst_report,
)
from equitylens.evidence_pipeline import (
    build_evidence_assessments,
)
from equitylens.guidance_pipeline import (
    build_equinor_guidance_report,
)
from equitylens.guidance_report import (
    GuidanceReport,
)
from equitylens.parser import parse_pdf


@dataclass(frozen=True)
class UnifiedResearchResult:
    analyst_report: AnalystReport
    guidance_report: GuidanceReport


def build_equinor_research_result(
    previous_source: PeriodSource,
    current_source: PeriodSource,
    company: str,
    ticker: str,
    metric_ids: tuple[str, ...],
) -> UnifiedResearchResult:
    """
    Build one unified deterministic research result
    from two Equinor reporting periods.

    Financial calculations, evidence assessment and
    guidance tracking remain delegated to their
    existing specialised pipelines.
    """

    if (
        previous_source.document.document_id
        == current_source.document.document_id
    ):
        raise ValueError(
            "Research pipeline requires two "
            "different documents."
        )

    dataset = (
        build_multi_period_financial_dataset(
            sources=(
                previous_source,
                current_source,
            ),
            metric_ids=metric_ids,
        )
    )

    previous_pages = parse_pdf(
        document_id=(
            previous_source.document.document_id
        ),
        pdf_path=(
            previous_source.document.local_path
        ),
    )

    current_pages = parse_pdf(
        document_id=(
            current_source.document.document_id
        ),
        pdf_path=(
            current_source.document.local_path
        ),
    )

    from_period = (
        previous_source.document.reporting_period
    )

    to_period = (
        current_source.document.reporting_period
    )

    evidence_assessments = (
        build_evidence_assessments(
            document_id=(
                current_source.document.document_id
            ),
            pages=current_pages,
            dataset=dataset,
            metric_ids=metric_ids,
            from_period=from_period,
            to_period=to_period,
        )
    )

    analyst_report = build_analyst_report(
        dataset=dataset,
        company=company,
        ticker=ticker,
        metric_ids=metric_ids,
        from_period=from_period,
        to_period=to_period,
        evidence_assessments=(
            evidence_assessments
        ),
    )

    guidance_report = (
        build_equinor_guidance_report(
            previous_document_id=(
                previous_source.document.document_id
            ),
            previous_pages=previous_pages,
            current_document_id=(
                current_source.document.document_id
            ),
            current_pages=current_pages,
        )
    )

    return UnifiedResearchResult(
        analyst_report=analyst_report,
        guidance_report=guidance_report,
    )