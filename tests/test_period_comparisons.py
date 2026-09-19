from decimal import Decimal

from equitylens.calculations import calculate_percentage_change
from equitylens.models import EvidenceRef, FinancialFact
from equitylens.periods import (
    classify_period_labels,
    parse_reporting_period,
)


def _fact(
    fact_id: str,
    period: str,
    value: int,
) -> FinancialFact:
    return FinancialFact(
        fact_id=fact_id,
        metric="Adjusted operating income",
        period=period,
        value=Decimal(value),
        unit="USD million",
        evidence=EvidenceRef(
            document_id=f"document-{fact_id}",
            page_number=4,
        ),
    )


def test_q4_to_q1_is_qoq():
    assert classify_period_labels(
        "Q4 2025",
        "Q1 2026",
    ) == "qoq"


def test_same_quarter_next_year_is_yoy():
    assert classify_period_labels(
        "Q2 2025",
        "Q2 2026",
    ) == "yoy"


def test_financial_change_classifies_qoq():
    q1 = _fact(
        fact_id="q1",
        period="Q1 2026",
        value=9770,
    )

    q2 = _fact(
        fact_id="q2",
        period="Q2 2026",
        value=11482,
    )

    change = calculate_percentage_change(
        current=q2,
        comparison=q1,
    )

    assert change.comparison_type == "qoq"


def test_financial_change_classifies_yoy():
    q2_2025 = _fact(
        fact_id="q2-2025",
        period="Q2 2025",
        value=6535,
    )

    q2_2026 = _fact(
        fact_id="q2-2026",
        period="Q2 2026",
        value=11482,
    )

    change = calculate_percentage_change(
        current=q2_2026,
        comparison=q2_2025,
    )

    assert change.comparison_type == "yoy"


def test_unknown_period_format_falls_back_to_other():
    assert classify_period_labels(
        "LTM 2025",
        "LTM 2026",
    ) == "other"


def test_existing_reporting_period_parser_still_works():
    period = parse_reporting_period("Q2 2026")

    assert period.year == 2026
    assert period.period_number == 2
    assert period.label == "Q2 2026"