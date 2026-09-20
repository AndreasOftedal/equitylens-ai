from equitylens.evidence_gate import (
    assess_sentence_evidence,
)
from equitylens.evidence_sentences import (
    EvidenceSentence,
)


def _sentence(
    text: str,
) -> EvidenceSentence:
    return EvidenceSentence(
        sentence_id="sentence-1",
        chunk_id="chunk-1",
        document_id="report",
        page_number=13,
        sentence_index=0,
        text=text,
        chunk_start_char=0,
        chunk_end_char=len(text),
        page_start_char=100,
        page_end_char=100 + len(text),
        section_context="Group review",
    )


def test_report_header_with_period_columns_is_non_narrative():
    result = assess_sentence_evidence(
        query="What drove production?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "13\n"
                "Exploration & Production Norway\n"
                "PRESS\n"
                "RELEASE\n"
                "SECOND QUARTER\n"
                "2026 REVIEW\n"
                "CONDENSED INTERIM FINANCIAL\n"
                "STATEMENTS AND NOTES\n"
                "SUPPLEMENTARY\n"
                "DISCLOSURES\n"
                "Equinor second quarter 2026\n"
                "Financial information\n"
                "Quarters\n"
                "Change\n"
                "First half\n"
                "(unaudited, in USD million)\n"
                "Q2 2026\n"
                "Q1 2026"
            
        ),
    )

    assert result.status == "non_narrative"


def test_supplementary_table_header_is_non_narrative():
    result = assess_sentence_evidence(
        query="What drove net operating income?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Items impacting net operating income/(loss) in\n"
                "the first quarter of 2026 (in USD million)\n"
                "Equinor\n"
                "Group\n"
                "E&P\n"
                "Norway\n"
                "E&P\n"
                "International E&P USA\n"
                "MMP\n"
                "Power\n"
                "Other\n"
                "44\n"
                "Supplementary disclosures\n"
                "PRESS\n"
                "RELEASE\n"
                "SECOND QUARTER\n"
                "2026 REVIEW\n"
                "CONDENSED INTERIM FINANCIAL\n"
                "STATEMENTS AND NOTES\n"
                "SUPPLEMENTARY\n"
                "DISCLOSURES\n"
                "Equinor second quarter 2026"
            
        ),
    )

    assert result.status == "non_narrative"


def test_real_aligned_management_sentence_remains_narrative():
    result = assess_sentence_evidence(
        query="What drove adjusted operating income?",
        expected_comparison_type="qoq",
        sentence=_sentence(
            
                "Adjusted operating income remained "
                "at a similar level compared to "
                "the prior quarter."
            
        ),
    )

    assert result.status == "aligned_context"


def test_real_direct_explanation_remains_narrative():
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