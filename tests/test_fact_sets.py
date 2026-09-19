from decimal import Decimal

import pytest

from equitylens.fact_sets import extract_registered_fact_set
from equitylens.models import ParsedTable


def _build_financial_table() -> ParsedTable:
    return ParsedTable(
        document_id="test-document",
        page_number=4,
        table_number=1,
        columns=(
            "Financial information",
            "Quarters.Q2 2026",
        ),
        rows=(
            (
                "Net operating income/(loss)",
                "12,993",
            ),
            (
                "Net income/(loss)",
                "4,836",
            ),
            (
                "Adjusted operating income*",
                "11,482",
            ),
            (
                "Adjusted net income*",
                "3,225",
            ),
        ),
    )


def test_extract_registered_fact_set_extracts_multiple_metrics():
    fact_set = extract_registered_fact_set(
        table=_build_financial_table(),
        metric_ids=(
            "net_operating_income",
            "net_income",
            "adjusted_operating_income",
            "adjusted_net_income",
        ),
        period="Q2 2026",
    )

    assert fact_set.document_id == "test-document"
    assert fact_set.period == "Q2 2026"
    assert len(fact_set.facts) == 4

    assert fact_set.get("net_operating_income").value == Decimal(12993)
    assert fact_set.get("net_income").value == Decimal(4836)

    assert (
        fact_set.get("adjusted_operating_income").value
        == Decimal(11482)
    )

    assert (
        fact_set.get("adjusted_net_income").value
        == Decimal(3225)
    )


def test_fact_set_preserves_individual_evidence():
    fact_set = extract_registered_fact_set(
        table=_build_financial_table(),
        metric_ids=(
            "net_operating_income",
            "adjusted_operating_income",
        ),
        period="Q2 2026",
    )

    adjusted_operating_income = fact_set.get(
        "adjusted_operating_income"
    )

    assert adjusted_operating_income.evidence.document_id == (
        "test-document"
    )

    assert adjusted_operating_income.evidence.page_number == 4
    assert adjusted_operating_income.evidence.table_number == 1

    assert adjusted_operating_income.evidence.row_label == (
        "Adjusted operating income*"
    )

    assert adjusted_operating_income.evidence.column_label == (
        "Quarters.Q2 2026"
    )


def test_extract_registered_fact_set_rejects_duplicate_metric_ids():
    with pytest.raises(
        ValueError,
        match="metric_ids must be unique",
    ):
        extract_registered_fact_set(
            table=_build_financial_table(),
            metric_ids=(
                "net_income",
                "net_income",
            ),
            period="Q2 2026",
        )


def test_extract_registered_fact_set_rejects_empty_metric_list():
    with pytest.raises(
        ValueError,
        match="metric_ids cannot be empty",
    ):
        extract_registered_fact_set(
            table=_build_financial_table(),
            metric_ids=(),
            period="Q2 2026",
        )