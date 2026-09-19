import pytest

from equitylens.documents import EQUINOR_Q2_2026
from equitylens.evidence_assessment import assess_retrieved_evidence
from equitylens.evidence_retrieval import NarrativeEvidenceRetriever
from equitylens.parser import parse_pdf
from equitylens.text_chunks import chunk_pages

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def retriever() -> NarrativeEvidenceRetriever:
    pages = parse_pdf(
        document_id=EQUINOR_Q2_2026.document_id,
        pdf_path=EQUINOR_Q2_2026.local_path,
    )

    chunks = chunk_pages(
        pages
    )

    return NarrativeEvidenceRetriever(
        chunks
    )


def _assess(
    retriever: NarrativeEvidenceRetriever,
    query: str,
):
    results = retriever.retrieve(
        query=query,
        top_k=60,
        candidate_k=60,
    )

    return assess_retrieved_evidence(
        query=query,
        expected_comparison_type="qoq",
        results=results,
    )


@pytest.mark.parametrize(
    "query",
    (
        "What drove cash flow?",
        "What drove production?",
        "What drove renewable power generation?",
        "What drove net operating income?",
    ),
)
def test_q2_report_does_not_invent_direct_qoq_explanations(
    retriever: NarrativeEvidenceRetriever,
    query: str,
):
    assessment = _assess(
        retriever=retriever,
        query=query,
    )

    assert (
        assessment.availability
        == "unavailable"
    )

    assert (
        assessment.direct_explanations
        == ()
    )


def test_adjusted_operating_income_has_context_but_no_direct_qoq_driver(
    retriever: NarrativeEvidenceRetriever,
):
    assessment = _assess(
        retriever=retriever,
        query=(
            "What drove adjusted operating income?"
        ),
    )

    assert (
        assessment.availability
        == "aligned_context_only"
    )

    assert (
        assessment.direct_explanations
        == ()
    )

    assert len(
        assessment.aligned_context
    ) >= 1

    assert any(
        "prior quarter"
        in evidence.sentence.text.lower()
        for evidence in assessment.aligned_context
    )


def test_production_driver_false_positive_is_rejected(
    retriever: NarrativeEvidenceRetriever,
):
    assessment = _assess(
        retriever=retriever,
        query="What drove production?",
    )

    accepted_text = " ".join(
        evidence.sentence.text.lower()
        for evidence in (
            assessment.direct_explanations
            + assessment.aligned_context
        )
    )

    assert (
        "gas sales volumes decreased"
        not in accepted_text
    )