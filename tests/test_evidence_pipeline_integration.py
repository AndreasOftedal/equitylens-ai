import pytest

from equitylens.analysis_pipeline import (
    PeriodSource,
    build_multi_period_financial_dataset,
)
from equitylens.documents import (
    EQUINOR_Q1_2026,
    EQUINOR_Q2_2026,
)
from equitylens.evidence_pipeline import (
    build_evidence_assessments,
)
from equitylens.parser import parse_pdf

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_operating_income",
    "net_income",
    "adjusted_operating_income",
    "adjusted_net_income",
)


@pytest.fixture(scope="module")
def dataset():
    return build_multi_period_financial_dataset(
        sources=(
            PeriodSource(
                document=EQUINOR_Q1_2026,
                page_number=4,
            ),
            PeriodSource(
                document=EQUINOR_Q2_2026,
                page_number=4,
            ),
        ),
        metric_ids=METRIC_IDS,
    )


@pytest.fixture(scope="module")
def evidence_assessments(
    dataset,
):
    pages = parse_pdf(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        pdf_path=(
            EQUINOR_Q2_2026.local_path
        ),
    )

    return build_evidence_assessments(
        document_id=(
            EQUINOR_Q2_2026.document_id
        ),
        pages=pages,
        dataset=dataset,
        metric_ids=METRIC_IDS,
        from_period="Q1 2026",
        to_period="Q2 2026",
        top_k=60,
        candidate_k=60,
    )


def test_real_pipeline_only_assesses_metrics_with_validated_queries(
    evidence_assessments,
):
    assert set(
        evidence_assessments
    ) == {
        "net_operating_income",
        "adjusted_operating_income",
    }


def test_real_pipeline_uses_qoq_financial_comparison(
    evidence_assessments,
):
    for assessment in (
        evidence_assessments.values()
    ):
        assert (
            assessment.expected_comparison_type
            == "qoq"
        )


def test_net_operating_income_has_no_direct_qoq_explanation(
    evidence_assessments,
):
    assessment = (
        evidence_assessments[
            "net_operating_income"
        ]
    )

    assert (
        assessment.availability
        == "unavailable"
    )

    assert (
        assessment.direct_explanations
        == ()
    )


def test_adjusted_operating_income_rejects_segment_context_for_group_metric(
    evidence_assessments,
):
    assessment = (
        evidence_assessments[
            "adjusted_operating_income"
        ]
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


def test_real_evidence_preserves_current_document_provenance(
    evidence_assessments,
):
    for assessment in (
        evidence_assessments.values()
    ):
        for evidence in (
            assessment.direct_explanations
            + assessment.aligned_context
        ):
            assert (
                evidence.sentence.document_id
                == EQUINOR_Q2_2026.document_id
            )

            assert (
                evidence.sentence.page_number
                >= 1
            )

            assert (
                evidence.sentence.text
            )