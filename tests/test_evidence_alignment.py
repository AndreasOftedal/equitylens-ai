from equitylens.evidence_alignment import (
    assess_period_alignment,
    detect_evidence_comparison_types,
)
from equitylens.text_chunks import TextChunk


def _chunk(
    text: str,
) -> TextChunk:
    return TextChunk(
        chunk_id="chunk",
        document_id="report",
        page_number=5,
        chunk_index=0,
        text=text,
        start_char=0,
        end_char=len(text),
    )


def test_detects_yoy_same_quarter_language():
    detected = (
        detect_evidence_comparison_types(
            
                "Production increased compared "
                "to the same quarter last year."
            
        )
    )

    assert detected == frozenset(
        {"yoy"}
    )


def test_detects_qoq_previous_quarter_language():
    detected = (
        detect_evidence_comparison_types(
            
                "Liquids prices increased compared "
                "with the previous quarter."
            
        )
    )

    assert detected == frozenset(
        {"qoq"}
    )


def test_detects_both_comparison_types():
    detected = (
        detect_evidence_comparison_types(
            
                "Revenue increased compared with "
                "the previous quarter and the same "
                "quarter last year."
            
        )
    )

    assert detected == frozenset(
        {
            "qoq",
            "yoy",
        }
    )


def test_detects_explicit_qoq_quarter_pair():
    detected = (
        detect_evidence_comparison_types(
            
                "The metric increased from "
                "Q1 2026 to Q2 2026."
            
        )
    )

    assert detected == frozenset(
        {"qoq"}
    )


def test_detects_explicit_yoy_quarter_pair():
    detected = (
        detect_evidence_comparison_types(
            
                "Q2 2026 increased compared "
                "with Q2 2025."
            
        )
    )

    assert detected == frozenset(
        {"yoy"}
    )


def test_aligned_evidence_is_identified():
    alignment = assess_period_alignment(
        expected_comparison_type="qoq",
        chunk=_chunk(
            
                "Cash flow increased compared "
                "with the previous quarter."
            
        ),
    )

    assert alignment.status == "aligned"
    assert (
        alignment.detected_comparison_types
        == frozenset({"qoq"})
    )


def test_mismatched_evidence_is_identified():
    alignment = assess_period_alignment(
        expected_comparison_type="qoq",
        chunk=_chunk(
            
                "Cash flow increased compared "
                "with the same quarter last year."
            
        ),
    )

    assert alignment.status == "mismatched"
    assert (
        alignment.detected_comparison_types
        == frozenset({"yoy"})
    )


def test_mixed_comparison_evidence_is_ambiguous():
    alignment = assess_period_alignment(
        expected_comparison_type="qoq",
        chunk=_chunk(
            
                "Production increased compared "
                "with the previous quarter and "
                "the same quarter last year."
            
        ),
    )

    assert alignment.status == "ambiguous"


def test_no_explicit_comparison_is_unknown():
    alignment = assess_period_alignment(
        expected_comparison_type="qoq",
        chunk=_chunk(
            
                "Strong production supported "
                "financial results."
            
        ),
    )

    assert alignment.status == "unknown"
    assert (
        alignment.detected_comparison_types
        == frozenset()
    )


def test_other_financial_comparison_is_unknown():
    alignment = assess_period_alignment(
        expected_comparison_type="other",
        chunk=_chunk(
            
                "Production increased compared "
                "with the same quarter last year."
            
        ),
    )

    assert alignment.status == "unknown"
    assert (
        alignment.detected_comparison_types
        == frozenset({"yoy"})
    )