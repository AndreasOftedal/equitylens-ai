import pytest

from equitylens.evidence_gate import (
    assess_sentence_evidence,
    extract_query_subject,
)
from equitylens.evidence_sentences import EvidenceSentence


def _sentence(
    text: str,
) -> EvidenceSentence:
    return EvidenceSentence(
        sentence_id="sentence-1",
        chunk_id="chunk-1",
        document_id="report",
        page_number=5,
        sentence_index=0,
        text=text,
        chunk_start_char=0,
        chunk_end_char=len(text),
        page_start_char=100,
        page_end_char=100 + len(text),
        section_context="Group review",
    )


def test_extracts_metric_subject_from_driver_query():
    assert extract_query_subject(
        "What drove adjusted operating income?"
    ) == "adjusted operating income"


def test_direct_qoq_explanation_is_usable():
    result = assess_sentence_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Cash flow increased compared with "
                "the previous quarter, primarily driven "
                "by higher commodity prices."
            
        ),
    )

    assert result.status == "direct_explanation"
    assert result.metric_match is True
    assert result.causal_signal is True
    assert (
        result.usable_as_direct_explanation
        is True
    )


def test_cause_first_explanation_is_usable():
    result = assess_sentence_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Higher commodity prices generated "
                "cash flow above the previous quarter."
            
        ),
    )

    assert result.status == "direct_explanation"
    assert result.metric_match is True


def test_aligned_statement_without_driver_is_context():
    result = assess_sentence_evidence(
        query=(
            "What drove adjusted operating income?"
        ),
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Adjusted operating income remained "
                "at a similar level compared to "
                "the prior quarter."
            
        ),
    )

    assert result.status == "aligned_context"
    assert result.metric_match is True
    assert result.causal_signal is False
    assert (
        result.usable_as_direct_explanation
        is False
    )


def test_yoy_evidence_is_rejected_for_qoq_analysis():
    result = assess_sentence_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Production increased compared to "
                "the same quarter last year, driven "
                "by new fields."
            
        ),
    )

    assert result.status == "period_mismatch"
    assert (
        result.usable_as_direct_explanation
        is False
    )


def test_multiple_period_bases_are_rejected():
    result = assess_sentence_evidence(
        query="What drove cash flow?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Cash flow increased compared with "
                "the previous quarter and the same "
                "quarter last year, driven by "
                "higher prices."
            
        ),
    )

    assert result.status == "period_ambiguous"


def test_sentence_without_period_basis_is_not_direct_evidence():
    result = assess_sentence_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Production was supported by "
                "new fields and new wells."
            
        ),
    )

    assert result.status == "period_unknown"


def test_aligned_but_wrong_metric_is_rejected():
    result = assess_sentence_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Adjusted operating income remained "
                "at a similar level compared to "
                "the prior quarter."
            
        ),
    )

    assert result.status == "query_mismatch"


def test_metric_mentioned_only_as_driver_is_rejected():
    result = assess_sentence_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Gas sales volumes decreased compared "
                "to the previous quarter due to seasonal "
                "maintenance, but increased compared to "
                "last year due to higher international "
                "gas production."
            
        ),
    )

    assert result.status == "query_mismatch"
    assert result.metric_match is False
    assert (
        result.usable_as_direct_explanation
        is False
    )


def test_net_operating_income_does_not_match_adjusted_operating_income():
    result = assess_sentence_evidence(
        query="What drove net operating income?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Adjusted operating income remained "
                "at a similar level compared to "
                "the prior quarter."
            
        ),
    )

    assert result.status == "query_mismatch"


def test_table_like_sentence_is_rejected():
    result = assess_sentence_evidence(
        query="What drove net operating income?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Net operating income Q2 2026 12,993 "
                "Q1 2026 8,784 Q2 2025 5,721 "
                "2026 21,776 2025 14,595 49%."
            
        ),
    )

    assert result.status == "non_narrative"


def test_other_comparison_type_is_unsupported():
    result = assess_sentence_evidence(
        query="What drove production?",
        expected_comparison_type="other",
        sentence=_sentence(
            
                "Production increased compared with "
                "the previous quarter, driven by "
                "new fields."
            
        ),
    )

    assert (
        result.status
        == "unsupported_comparison"
    )


def test_empty_query_is_rejected():
    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        extract_query_subject(" ")