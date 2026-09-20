import pytest

from equitylens.analysis_pipeline import (
    PeriodSource,
    build_multi_period_financial_dataset,
)
from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
)
from equitylens.evidence_pipeline import (
    build_evidence_assessments,
)
from equitylens.parser import parse_pdf

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "operating_cash_flow",
    "total_equity_production",
)


@pytest.fixture(scope="module")
def evidence_assessments():
    dataset = build_multi_period_financial_dataset(
        sources=(
            PeriodSource(
                document=AKER_BP_Q1_2026,
                page_number=3,
            ),
            PeriodSource(
                document=AKER_BP_Q2_2026,
                page_number=3,
            ),
        ),
        metric_ids=METRIC_IDS,
    )

    pages = parse_pdf(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        pdf_path=(
            AKER_BP_Q2_2026.local_path
        ),
    )

    return build_evidence_assessments(
        document_id=(
            AKER_BP_Q2_2026.document_id
        ),
        pages=pages,
        dataset=dataset,
        metric_ids=METRIC_IDS,
        from_period="Q1 2026",
        to_period="Q2 2026",
        top_k=60,
        candidate_k=60,
    )


def test_aker_bp_cash_flow_remains_conservative_without_explicit_qoq_basis(
    evidence_assessments,
):
    assessment = evidence_assessments[
        "operating_cash_flow"
    ]

    assert (
        assessment.expected_comparison_type
        == "qoq"
    )

    assert (
        assessment.availability
        == "unavailable"
    )

    assert (
        assessment.direct_explanations
        == ()
    )

    assert (
        assessment.aligned_context
        == ()
    )

    rejection_counts = dict(
        assessment.rejection_counts
    )

    assert (
        rejection_counts[
            "period_unknown"
        ]
        >= 1
    )


def test_aker_bp_group_production_rejects_asset_level_explanations(
    evidence_assessments,
):
    assessment = evidence_assessments[
        "total_equity_production"
    ]

    assert (
        assessment.expected_comparison_type
        == "qoq"
    )

    assert (
        assessment.availability
        == "unavailable"
    )

    assert (
        assessment.direct_explanations
        == ()
    )

    assert (
        assessment.aligned_context
        == ()
    )

    rejection_counts = dict(
        assessment.rejection_counts
    )

    assert (
        rejection_counts[
            "scope_mismatch"
        ]
        >= 1
    )


def test_aker_bp_production_scope_guard_rejects_multiple_asset_sections(
    evidence_assessments,
):
    assessment = evidence_assessments[
        "total_equity_production"
    ]

    rejection_counts = dict(
        assessment.rejection_counts
    )

    assert (
        rejection_counts[
            "scope_mismatch"
        ]
        >= 4
    )