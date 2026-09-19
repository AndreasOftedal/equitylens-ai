from decimal import Decimal

from equitylens.financial_extractor import (
    extract_registered_financial_fact,
)
from equitylens.models import ParsedTable


def test_extract_registered_financial_fact_uses_canonical_metric():
    table = ParsedTable(
        document_id="test-document",
        page_number=4,
        table_number=1,
        columns=(
            "Financial information",
            "Quarters.Q2 2026",
        ),
        rows=(
            (
                "Adjusted operating income/(loss)*",
                "11,482",
            ),
        ),
    )

    fact = extract_registered_financial_fact(
        table=table,
        metric_id="adjusted_operating_income",
        period="Q2 2026",
    )

    assert fact.fact_id == (
        "test-document-adjusted_operating_income-q2-2026"
    )

    assert fact.metric == "Adjusted operating income"
    assert fact.period == "Q2 2026"
    assert fact.value == Decimal(11482)
    assert fact.unit == "USD million"

    assert fact.evidence.document_id == "test-document"
    assert fact.evidence.page_number == 4
    assert fact.evidence.table_number == 1

    assert fact.evidence.row_label == (
        "Adjusted operating income/(loss)*"
    )

    assert fact.evidence.column_label == "Quarters.Q2 2026"


def test_extract_registered_financial_fact_accepts_alternate_source_label():
    table = ParsedTable(
        document_id="test-document",
        page_number=4,
        table_number=1,
        columns=(
            "Financial information",
            "Q1 2026",
        ),
        rows=(
            (
                "Adjusted operating income*",
                "9,770",
            ),
        ),
    )

    fact = extract_registered_financial_fact(
        table=table,
        metric_id="adjusted_operating_income",
        period="Q1 2026",
    )

    assert fact.metric == "Adjusted operating income"
    assert fact.value == Decimal(9770)
    assert fact.unit == "USD million"

    assert fact.evidence.row_label == (
        "Adjusted operating income*"
    )