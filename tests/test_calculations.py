from decimal import Decimal

from equitylens.calculations import calculate_percentage_change
from equitylens.models import EvidenceRef, FinancialFact


def test_calculate_adjusted_operating_income_yoy_change():
    q2_2026 = FinancialFact(
        fact_id="adjusted-operating-income-q2-2026",
        metric="Adjusted operating income*",
        period="Q2 2026",
        value=Decimal(11482),
        unit="USD million",
        evidence=EvidenceRef(
            document_id="equinor-q2-2026",
            page_number=4,
            table_number=1,
            row_label="Adjusted operating income*",
            column_label="Q2 2026",
        ),
    )

    q2_2025 = FinancialFact(
        fact_id="adjusted-operating-income-q2-2025",
        metric="Adjusted operating income*",
        period="Q2 2025",
        value=Decimal(6535),
        unit="USD million",
        evidence=EvidenceRef(
            document_id="equinor-q2-2026",
            page_number=4,
            table_number=1,
            row_label="Adjusted operating income*",
            column_label="Q2 2025",
        ),
    )

    change = calculate_percentage_change(
        current=q2_2026,
        comparison=q2_2025,
    )

    assert change.metric == "Adjusted operating income*"
    assert change.from_period == "Q2 2025"
    assert change.to_period == "Q2 2026"

    assert change.from_value == Decimal(6535)
    assert change.to_value == Decimal(11482)

    assert change.absolute_change == Decimal(4947)
    assert change.percentage_change == Decimal("75.7")

    assert change.unit == "USD million"

    assert change.source_fact_ids == (
        "adjusted-operating-income-q2-2025",
        "adjusted-operating-income-q2-2026",
    )