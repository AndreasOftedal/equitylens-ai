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
    "adjusted_operating_income",
    "adjusted_net_income",
)


def test_real_reports_build_multi_metric_multi_period_dataset():
    dataset = build_multi_period_financial_dataset(
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

    assert dataset.get_fact(
        "net_operating_income",
        "Q1 2026",
    ).value == Decimal(8784)

    assert dataset.get_fact(
        "net_operating_income",
        "Q2 2026",
    ).value == Decimal(12993)

    assert dataset.get_fact(
        "net_income",
        "Q1 2026",
    ).value == Decimal(3105)

    assert dataset.get_fact(
        "net_income",
        "Q2 2026",
    ).value == Decimal(4836)

    assert dataset.get_fact(
        "adjusted_operating_income",
        "Q1 2026",
    ).value == Decimal(9770)

    assert dataset.get_fact(
        "adjusted_operating_income",
        "Q2 2026",
    ).value == Decimal(11482)

    assert dataset.get_fact(
        "adjusted_net_income",
        "Q1 2026",
    ).value == Decimal(3695)

    assert dataset.get_fact(
        "adjusted_net_income",
        "Q2 2026",
    ).value == Decimal(3225)


def test_real_reports_compare_multiple_metrics():
    dataset = build_multi_period_financial_dataset(
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

    changes = dataset.compare_metrics(
        metric_ids=METRIC_IDS,
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    changes_by_metric = {
        change.metric: change
        for change in changes
    }

    net_operating_income = changes_by_metric[
        "Net operating income"
    ]

    assert net_operating_income.absolute_change == Decimal(4209)
    assert net_operating_income.percentage_change == Decimal("47.9")

    net_income = changes_by_metric["Net income"]

    assert net_income.absolute_change == Decimal(1731)
    assert net_income.percentage_change == Decimal("55.7")

    adjusted_operating_income = changes_by_metric[
        "Adjusted operating income"
    ]

    assert adjusted_operating_income.absolute_change == Decimal(1712)
    assert adjusted_operating_income.percentage_change == Decimal("17.5")

    adjusted_net_income = changes_by_metric[
        "Adjusted net income"
    ]

    assert adjusted_net_income.absolute_change == Decimal(-470)
    assert adjusted_net_income.percentage_change == Decimal("-12.7")


def test_real_dataset_preserves_document_lineage():
    dataset = build_multi_period_financial_dataset(
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

    q1_fact = dataset.get_fact(
        "adjusted_operating_income",
        "Q1 2026",
    )

    q2_fact = dataset.get_fact(
        "adjusted_operating_income",
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