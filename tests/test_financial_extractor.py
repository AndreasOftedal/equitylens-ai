from decimal import Decimal

from equitylens.financial_extractor import extract_exchange_rate_fact
from equitylens.models import ParsedTable


def test_extract_usd_nok_average_rate_q2_2026():
    table = ParsedTable(
        document_id="equinor-q2-2026-financial-statements-and-review",
        page_number=39,
        table_number=1,
        columns=(
            "Exchange rates",
            "Quarters.Q2 2026",
            "Quarters.Q1 2026",
            "Quarters.Q2 2025",
            "Change.Q2 on Q2",
            "First half.2026",
            "First half.2025",
            "Change",
            "Full year.2025",
            "Change.Q2 on FY",
        ),
        rows=(
            (
                "USD/NOK",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ),
            (
                "Average daily rate",
                "9.4240",
                "9.7267",
                "10.2974",
                "(8%)",
                "9.5803",
                "10.7006",
                "(10%)",
                "10.3912",
                "(9%)",
            ),
            (
                "Period-end rate",
                "9.9267",
                "9.7517",
                "10.0977",
                "(2%)",
                "9.9267",
                "10.0977",
                "(2%)",
                "10.0791",
                "(2%)",
            ),
            (
                "EUR/USD",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ),
        ),
    )

    fact = extract_exchange_rate_fact(
        table=table,
        currency_pair="USD/NOK",
        measure="Average daily rate",
        period="Q2 2026",
    )

    assert fact.metric == "USD/NOK Average daily rate"
    assert fact.period == "Q2 2026"
    assert fact.value == Decimal("9.4240")
    assert fact.unit == "NOK per USD"

    assert fact.evidence.document_id == table.document_id
    assert fact.evidence.page_number == 39
    assert fact.evidence.table_number == 1
    assert fact.evidence.row_label == "USD/NOK / Average daily rate"
    assert fact.evidence.column_label == "Quarters.Q2 2026"