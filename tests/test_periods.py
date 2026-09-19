import pytest

from equitylens.periods import (
    ReportingPeriod,
    classify_period_comparison,
    parse_reporting_period,
)


def test_parse_quarter():
    period = parse_reporting_period("Q2 2026")

    assert period == ReportingPeriod(
        year=2026,
        period_type="quarter",
        period_number=2,
    )

    assert period.label == "Q2 2026"


def test_parse_half_year():
    period = parse_reporting_period("H1 2026")

    assert period.year == 2026
    assert period.period_type == "half_year"
    assert period.period_number == 1
    assert period.label == "H1 2026"


def test_parse_full_year():
    period = parse_reporting_period("FY 2026")

    assert period.year == 2026
    assert period.period_type == "full_year"
    assert period.period_number is None
    assert period.label == "FY 2026"


def test_classify_qoq_comparison():
    assert classify_period_comparison(
        parse_reporting_period("Q1 2026"),
        parse_reporting_period("Q2 2026"),
    ) == "qoq"


def test_classify_yoy_comparison():
    assert classify_period_comparison(
        parse_reporting_period("Q2 2025"),
        parse_reporting_period("Q2 2026"),
    ) == "yoy"


def test_non_standard_comparison_is_other():
    assert classify_period_comparison(
        parse_reporting_period("Q1 2025"),
        parse_reporting_period("Q3 2026"),
    ) == "other"


def test_invalid_quarter_is_rejected():
    with pytest.raises(
        ValueError,
        match="Quarter must be between 1 and 4",
    ):
        parse_reporting_period("Q5 2026")