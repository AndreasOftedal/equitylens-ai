from decimal import Decimal

import pytest

from equitylens.analysis_pipeline import (
    PeriodSource,
    build_multi_period_financial_dataset,
)
from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
)

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_income",
    "basic_earnings_per_share",
    "operating_cash_flow",
    "total_equity_production",
)


EXPECTED_VALUES = {
    "Q1 2026": {
        "net_income": Decimal(758),
        "basic_earnings_per_share": Decimal("1.20"),
        "operating_cash_flow": Decimal(2013),
        "total_equity_production": Decimal("398.4"),
    },
    "Q2 2026": {
        "net_income": Decimal(521),
        "basic_earnings_per_share": Decimal("0.82"),
        "operating_cash_flow": Decimal(3123),
        "total_equity_production": Decimal("383.6"),
    },
}


EXPECTED_QOQ_CHANGES = {
    "Net income": (
        Decimal(-237),
        Decimal("-31.3"),
    ),
    "Basic earnings per share": (
        Decimal("-0.38"),
        Decimal("-31.7"),
    ),
    "Cash flows provided by operating activities": (
        Decimal(1110),
        Decimal("55.1"),
    ),
    "Total equity liquids and gas production": (
        Decimal("-14.8"),
        Decimal("-3.7"),
    ),
}


def _build_dataset():
    return build_multi_period_financial_dataset(
        sources=(
            PeriodSource(
                document=AKER_BP_Q1_2026,
                page_number=3,
            ),
            PeriodSource(
                document=AKER_BP_Q2_2026,
                page_number=3,
            ),
        ),
        metric_ids=METRIC_IDS,
    )


def test_aker_bp_reports_extract_registered_metrics():
    dataset = _build_dataset()

    for period, expected_metrics in EXPECTED_VALUES.items():
        for metric_id, expected_value in expected_metrics.items():
            fact = dataset.get_fact(
                metric_id,
                period,
            )

            assert fact.value == expected_value


def test_aker_bp_reports_calculate_qoq_changes():
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


def test_aker_bp_dataset_preserves_source_provenance():
    dataset = _build_dataset()

    expected_documents = {
        "Q1 2026": AKER_BP_Q1_2026.document_id,
        "Q2 2026": AKER_BP_Q2_2026.document_id,
    }

    for period, document_id in expected_documents.items():
        for metric_id in METRIC_IDS:
            fact = dataset.get_fact(
                metric_id,
                period,
            )

            assert (
                fact.evidence.document_id
                == document_id
            )

            assert fact.evidence.page_number == 3
            assert fact.evidence.table_number == 1
            assert fact.evidence.row_label is not None
            assert fact.evidence.column_label == period


def test_aker_bp_dataset_uses_expected_units():
    dataset = _build_dataset()

    expected_units = {
        "net_income": "USD million",
        "basic_earnings_per_share": "USD per share",
        "operating_cash_flow": "USD million",
        "total_equity_production": "mboe/day",
    }

    for metric_id, expected_unit in expected_units.items():
        assert dataset.get_fact(
            metric_id,
            "Q2 2026",
        ).unit == expected_unit