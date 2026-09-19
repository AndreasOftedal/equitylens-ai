import pytest

from equitylens.evidence_assessment import (
    assess_retrieved_evidence,
)
from equitylens.narrative_reranker import (
    RerankedResult,
)
from equitylens.text_chunks import TextChunk


def _result(
    text: str,
    rank: int = 1,
    page_number: int = 5,
    chunk_id: str = "chunk-1",
    start_char: int = 0,
) -> RerankedResult:
    chunk = TextChunk(
        chunk_id=chunk_id,
        document_id="report",
        page_number=page_number,
        chunk_index=rank - 1,
        text=text,
        start_char=start_char,
        end_char=start_char + len(text),
        section_context="Group review",
    )

    return RerankedResult(
        chunk=chunk,
        retrieval_score=5.0,
        narrative_score=2.0,
        scope_score=1.0,
        final_score=8.0,
        rank=rank,
    )


def test_direct_explanation_is_exposed():
    assessment = assess_retrieved_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        results=(
            _result(
                
                    "Cash flow increased compared with "
                    "the previous quarter, primarily driven "
                    "by higher commodity prices."
                
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

    assert (
        assessment.direct_explanations[
            0
        ].gate.usable_as_direct_explanation
        is True
    )


def test_aligned_context_only_is_reported():
    assessment = assess_retrieved_evidence(
        query=(
            "What drove adjusted operating income?"
        ),
        expected_comparison_type="qoq",
        results=(
            _result(
                
                    "Adjusted operating income remained "
                    "at a similar level compared to "
                    "the prior quarter."
                
            ),
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
    ) == 1


def test_unavailable_when_only_mismatched_evidence_exists():
    assessment = assess_retrieved_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        results=(
            _result(
                
                    "Production increased compared with "
                    "the same quarter last year, driven "
                    "by new fields."
                
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
        assessment.aligned_context
        == ()
    )

    assert dict(
        assessment.rejection_counts
    )["period_mismatch"] == 1


def test_wrong_metric_is_counted_as_rejection():
    assessment = assess_retrieved_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        results=(
            _result(
                
                    "Adjusted operating income remained "
                    "at a similar level compared to "
                    "the prior quarter."
                
            ),
        ),
    )

    assert (
        assessment.availability
        == "unavailable"
    )

    assert dict(
        assessment.rejection_counts
    )["query_mismatch"] == 1


def test_overlapping_duplicate_sentence_is_deduplicated():
    text = (
        "Cash flow increased compared with "
        "the previous quarter, primarily driven "
        "by higher commodity prices."
    )

    assessment = assess_retrieved_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        results=(
            _result(
                text=text,
                rank=1,
                chunk_id="chunk-a",
                start_char=100,
            ),
            _result(
                text=text,
                rank=2,
                chunk_id="chunk-b",
                start_char=100,
            ),
        ),
    )

    assert len(
        assessment.direct_explanations
    ) == 1

    assert (
        assessment.direct_explanations[
            0
        ].chunk_rank
        == 1
    )


def test_empty_retrieval_result_is_unavailable():
    assessment = assess_retrieved_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        results=(),
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

    assert (
        assessment.rejection_counts
        == ()
    )


def test_assessment_preserves_sentence_provenance():
    assessment = assess_retrieved_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        results=(
            _result(
                (
                    "Cash flow increased compared with "
                    "the previous quarter, primarily driven "
                    "by higher prices."
                ),
                page_number=9,
                start_char=250,
            ),
        ),
    )

    evidence = (
        assessment.direct_explanations[
            0
        ]
    )

    assert (
        evidence.sentence.document_id
        == "report"
    )

    assert (
        evidence.sentence.page_number
        == 9
    )

    assert (
        evidence.sentence.page_start_char
        == 250
    )


def test_empty_query_is_rejected():
    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        assess_retrieved_evidence(
            query=" ",
            expected_comparison_type="qoq",
            results=(),
        )