from equitylens.evidence_assessment import (
    assess_retrieved_evidence,
)
from equitylens.narrative_reranker import (
    RerankedResult,
)
from equitylens.text_chunks import TextChunk


def _result(
    text: str,
) -> RerankedResult:
    chunk = TextChunk(
        chunk_id="chunk-1",
        document_id="report",
        page_number=7,
        chunk_index=0,
        text=text,
        start_char=100,
        end_char=100 + len(text),
        section_context="Operational review",
    )

    return RerankedResult(
        chunk=chunk,
        retrieval_score=5.0,
        narrative_score=2.0,
        scope_score=1.0,
        final_score=8.0,
        rank=1,
    )


def _assess(
    text: str,
):
    return assess_retrieved_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        results=(
            _result(text),
        ),
    )


def test_adjacent_valid_context_is_accepted():
    assessment = _assess(
        
            "Production decreased compared with "
            "the previous quarter. "
            "The decrease was primarily due to "
            "planned maintenance."
        
    )

    assert (
        assessment.availability
        == "direct_explanation"
    )

    assert len(
        assessment.direct_explanations
    ) == 1

    evidence = (
        assessment.direct_explanations[0]
    )

    assert len(
        evidence.context_sentences
    ) == 1

    assert (
        "previous quarter"
        in evidence.context_sentences[
            0
        ].text.lower()
    )


def test_context_is_not_inherited_across_intervening_sentence():
    assessment = _assess(
        
            "Production decreased compared with "
            "the previous quarter. "
            "Operations remained stable during June. "
            "The decrease was primarily due to "
            "planned maintenance."
        
    )

    assert (
        assessment.availability
        == "aligned_context_only"
    )

    assert (
        assessment.direct_explanations
        == ()
    )


def test_mismatched_period_context_cannot_support_direct_explanation():
    assessment = _assess(
        
            "Production decreased compared with "
            "the same quarter last year. "
            "The decrease was primarily due to "
            "planned maintenance."
        
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
        )["period_mismatch"]
        >= 1
    )


def test_non_causal_following_sentence_is_not_promoted():
    assessment = _assess(
        
            "Production decreased compared with "
            "the previous quarter. "
            "The decrease continued during June."
        
    )

    assert (
        assessment.availability
        == "aligned_context_only"
    )

    assert (
        assessment.direct_explanations
        == ()
    )


def test_non_anaphoric_causal_sentence_is_not_promoted():
    assessment = _assess(
        
            "Production decreased compared with "
            "the previous quarter. "
            "Lower facility uptime was primarily due to "
            "planned maintenance."
        
    )

    assert (
        assessment.availability
        == "aligned_context_only"
    )

    assert (
        assessment.direct_explanations
        == ()
    )


def test_causal_sentence_with_its_own_period_is_not_inherited():
    assessment = _assess(
        
            "Production decreased compared with "
            "the previous quarter. "
            "The decrease was primarily due to maintenance "
            "compared with the same quarter last year."
        
    )

    assert (
        assessment.availability
        == "aligned_context_only"
    )

    assert (
        assessment.direct_explanations
        == ()
    )