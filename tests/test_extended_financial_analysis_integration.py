from decimal import Decimal

import pytest

from equitylens.analysis_pipeline import (
    PeriodSource,
    build_multi_period_financial_dataset,
)
from equitylens.documents import EQUINOR_Q1_2026, EQUINOR_Q2_2026

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_operating_income",
    "net_income",
    "basic_earnings_per_share",
    "adjusted_operating_income",
    "adjusted_net_income",
    "adjusted_earnings_per_share",
    "operating_cash_flow",
    "operating_cash_flow_after_tax",
    "net_cash_flow_before_capital_distribution",
    "group_average_liquids_price",
    "total_equity_production",
    "total_power_generation",
    "renewable_power_generation",
)


EXPECTED_VALUES = {
    "Q1 2026": {
        "net_operating_income": Decimal(8784),
        "net_income": Decimal(3105),
        "basic_earnings_per_share": Decimal("1.24"),
        "adjusted_operating_income": Decimal(9770),
        "adjusted_net_income": Decimal(3695),
        "adjusted_earnings_per_share": Decimal("1.48"),
        "operating_cash_flow": Decimal(5213),
        "operating_cash_flow_after_tax": Decimal(6019),
        "net_cash_flow_before_capital_distribution": Decimal(2947),
        "group_average_liquids_price": Decimal("78.6"),
        "total_equity_production": Decimal(2313),
        "total_power_generation": Decimal("1.39"),
        "renewable_power_generation": Decimal("0.98"),
    },
    "Q2 2026": {
        "net_operating_income": Decimal(12993),
        "net_income": Decimal(4836),
        "basic_earnings_per_share": Decimal("1.99"),
        "adjusted_operating_income": Decimal(11482),
        "adjusted_net_income": Decimal(3225),
        "adjusted_earnings_per_share": Decimal("1.33"),
        "operating_cash_flow": Decimal(9470),
        "operating_cash_flow_after_tax": Decimal(7677),
        "net_cash_flow_before_capital_distribution": Decimal(5484),
        "group_average_liquids_price": Decimal("97.9"),
        "total_equity_production": Decimal(2165),
        "total_power_generation": Decimal("1.19"),
        "renewable_power_generation": Decimal("0.91"),
    },
}


EXPECTED_QOQ_CHANGES = {
    "Net operating income": (
        Decimal(4209),
        Decimal("47.9"),
    ),
    "Net income": (
        Decimal(1731),
        Decimal("55.7"),
    ),
    "Basic earnings per share": (
        Decimal("0.75"),
        Decimal("60.5"),
    ),
    "Adjusted operating income": (
        Decimal(1712),
        Decimal("17.5"),
    ),
    "Adjusted net income": (
        Decimal(-470),
        Decimal("-12.7"),
    ),
    "Adjusted earnings per share": (
        Decimal("-0.15"),
        Decimal("-10.1"),
    ),
    "Cash flows provided by operating activities": (
        Decimal(4257),
        Decimal("81.7"),
    ),
    "Cash flow from operations after taxes paid": (
        Decimal(1658),
        Decimal("27.5"),
    ),
    "Net cash flow before capital distribution": (
        Decimal(2537),
        Decimal("86.1"),
    ),
    "Group average liquids price": (
        Decimal("19.3"),
        Decimal("24.6"),
    ),
    "Total equity liquids and gas production": (
        Decimal(-148),
        Decimal("-6.4"),
    ),
    "Total power generation": (
        Decimal("-0.20"),
        Decimal("-14.4"),
    ),
    "Renewable power generation": (
        Decimal("-0.07"),
        Decimal("-7.1"),
    ),
}


def _build_dataset():
    return build_multi_period_financial_dataset(
        sources=(
            PeriodSource(
                document=EQUINOR_Q1_2026,
                page_number=4,
            ),
            PeriodSource(
                document=EQUINOR_Q2_2026,
                page_number=4,
            ),
        ),
        metric_ids=METRIC_IDS,
    )


def test_real_reports_extract_all_registered_analyst_metrics():
    dataset = _build_dataset()

    for period, expected_metrics in EXPECTED_VALUES.items():
        for metric_id, expected_value in expected_metrics.items():
            fact = dataset.get_fact(
                metric_id,
                period,
            )

            assert fact.value == expected_value


def test_real_reports_calculate_all_qoq_changes():
    dataset = _build_dataset()

    changes = dataset.compare_metrics(
        metric_ids=METRIC_IDS,
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    assert len(changes) == len(METRIC_IDS)

    changes_by_metric = {
        change.metric: change
        for change in changes
    }

    assert set(changes_by_metric) == set(
        EXPECTED_QOQ_CHANGES
    )

    for metric, (
        expected_absolute_change,
        expected_percentage_change,
    ) in EXPECTED_QOQ_CHANGES.items():
        change = changes_by_metric[metric]

        assert (
            change.absolute_change
            == expected_absolute_change
        )

        assert (
            change.percentage_change
            == expected_percentage_change
        )

        assert change.comparison_type == "qoq"


def test_extended_dataset_preserves_source_provenance():
    dataset = _build_dataset()

    for metric_id in METRIC_IDS:
        q1_fact = dataset.get_fact(
            metric_id,
            "Q1 2026",
        )

        q2_fact = dataset.get_fact(
            metric_id,
            "Q2 2026",
        )

        assert q1_fact.evidence.document_id == (
            EQUINOR_Q1_2026.document_id
        )

        assert q2_fact.evidence.document_id == (
            EQUINOR_Q2_2026.document_id
        )

        assert q1_fact.evidence.page_number == 4
        assert q2_fact.evidence.page_number == 4

        assert q1_fact.evidence.table_number is not None
        assert q2_fact.evidence.table_number is not None

        assert q1_fact.evidence.row_label is not None
        assert q2_fact.evidence.row_label is not None


def test_extended_dataset_uses_expected_units():
    dataset = _build_dataset()

    expected_units = {
        "net_operating_income": "USD million",
        "net_income": "USD million",
        "basic_earnings_per_share": "USD per share",
        "adjusted_operating_income": "USD million",
        "adjusted_net_income": "USD million",
        "adjusted_earnings_per_share": "USD per share",
        "operating_cash_flow": "USD million",
        "operating_cash_flow_after_tax": "USD million",
        "net_cash_flow_before_capital_distribution": "USD million",
        "group_average_liquids_price": "USD/bbl",
        "total_equity_production": "mboe/day",
        "total_power_generation": "TWh",
        "renewable_power_generation": "TWh",
    }

    for metric_id, expected_unit in expected_units.items():
        assert dataset.get_fact(
            metric_id,
            "Q2 2026",
        ).unit == expected_unit