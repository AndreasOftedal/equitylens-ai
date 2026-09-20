from equitylens.documents import (
    AKER_BP_Q2_2026,
)
from equitylens.evidence_assessment import (
    assess_retrieved_evidence,
)
from equitylens.narrative_reranker import (
    RerankedResult,
)
from equitylens.text_chunks import TextChunk


def _result(
    text: str,
    section_context: str,
    document_id: str = AKER_BP_Q2_2026.document_id,
) -> RerankedResult:
    chunk = TextChunk(
        chunk_id="chunk-1",
        document_id=document_id,
        page_number=7,
        chunk_index=0,
        text=text,
        start_char=100,
        end_char=100 + len(text),
        section_context=section_context,
    )

    return RerankedResult(
        chunk=chunk,
        retrieval_score=5.0,
        narrative_score=2.0,
        scope_score=1.0,
        final_score=8.0,
        rank=1,
    )


def test_group_metric_rejects_asset_level_direct_explanation():
    assessment = assess_retrieved_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        metric_scope="group",
        results=(
            _result(
                text=(
                    "Production decreased compared with "
                    "the previous quarter, primarily due "
                    "to natural production decline."
                ),
                section_context=(
                    "7 · Aker BP Quarterly Report · "
                    "Q2 2026 OPERATIONAL REVIEW "
                    "Alvheim area KEY FIGURES"
                ),
            ),
        ),
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
        dict(
            assessment.rejection_counts
        )["scope_mismatch"]
        == 1
    )


def test_group_metric_rejects_asset_level_adjacent_explanation():
    assessment = assess_retrieved_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        metric_scope="group",
        results=(
            _result(
                text=(
                    "Production decreased compared with "
                    "the previous quarter. "
                    "The decrease was primarily due to "
                    "natural production decline."
                ),
                section_context=(
                    "7 · Aker BP Quarterly Report · "
                    "Q2 2026 OPERATIONAL REVIEW "
                    "Alvheim area KEY FIGURES"
                ),
            ),
        ),
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
        dict(
            assessment.rejection_counts
        )["scope_mismatch"]
        >= 1
    )


def test_group_metric_accepts_group_level_direct_explanation():
    assessment = assess_retrieved_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        metric_scope="group",
        results=(
            _result(
                text=(
                    "Cash flow increased compared with "
                    "the previous quarter, primarily driven "
                    "by higher income."
                ),
                section_context=(
                    "6 · Aker BP Quarterly Report · "
                    "Q2 2026 Cash flow (USD MILLION)"
                ),
            ),
        ),
    )

    assert (
        assessment.availability
        == "direct_explanation"
    )

    assert len(
        assessment.direct_explanations
    ) == 1


def test_unknown_scope_does_not_become_direct_explanation():
    assessment = assess_retrieved_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        metric_scope="group",
        results=(
            _result(
                text=(
                    "Production decreased compared with "
                    "the previous quarter, primarily due "
                    "to maintenance."
                ),
                section_context="Operational review",
                document_id="unknown-report",
            ),
        ),
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
        dict(
            assessment.rejection_counts
        )["scope_unknown"]
        == 1
    )