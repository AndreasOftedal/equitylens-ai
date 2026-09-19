from decimal import Decimal

import pytest

from equitylens.fact_sets import FinancialFactSet
from equitylens.financial_dataset import MultiPeriodFinancialDataset
from equitylens.models import EvidenceRef, FinancialFact


def _fact(
    fact_id: str,
    metric: str,
    period: str,
    value: int,
) -> FinancialFact:
    return FinancialFact(
        fact_id=fact_id,
        metric=metric,
        period=period,
        value=Decimal(value),
        unit="USD million",
        evidence=EvidenceRef(
            document_id=f"document-{period.lower().replace(' ', '-')}",
            page_number=4,
            table_number=1,
            row_label=metric,
            column_label=period,
        ),
    )


def _build_dataset() -> MultiPeriodFinancialDataset:
    q1 = FinancialFactSet(
        document_id="document-q1-2026",
        period="Q1 2026",
        facts=(
            _fact(
                "q1-net-operating-income",
                "Net operating income",
                "Q1 2026",
                8784,
            ),
            _fact(
                "q1-adjusted-operating-income",
                "Adjusted operating income",
                "Q1 2026",
                9770,
            ),
        ),
    )

    q2 = FinancialFactSet(
        document_id="document-q2-2026",
        period="Q2 2026",
        facts=(
            _fact(
                "q2-net-operating-income",
                "Net operating income",
                "Q2 2026",
                12993,
            ),
            _fact(
                "q2-adjusted-operating-income",
                "Adjusted operating income",
                "Q2 2026",
                11482,
            ),
        ),
    )

    return MultiPeriodFinancialDataset(
        fact_sets=(
            q1,
            q2,
        )
    )


def test_dataset_gets_fact_by_metric_and_period():
    dataset = _build_dataset()

    fact = dataset.get_fact(
        metric_id="adjusted_operating_income",
        period="Q2 2026",
    )

    assert fact.value == Decimal(11482)
    assert fact.period == "Q2 2026"


def test_dataset_compares_one_metric_across_periods():
    dataset = _build_dataset()

    change = dataset.compare(
        metric_id="adjusted_operating_income",
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    assert change.from_value == Decimal(9770)
    assert change.to_value == Decimal(11482)
    assert change.absolute_change == Decimal(1712)
    assert change.percentage_change == Decimal("17.5")

    assert change.source_fact_ids == (
        "q1-adjusted-operating-income",
        "q2-adjusted-operating-income",
    )


def test_dataset_compares_multiple_metrics():
    dataset = _build_dataset()

    changes = dataset.compare_metrics(
        metric_ids=(
            "net_operating_income",
            "adjusted_operating_income",
        ),
        from_period="Q1 2026",
        to_period="Q2 2026",
    )

    assert len(changes) == 2

    assert changes[0].metric == "Net operating income"
    assert changes[0].absolute_change == Decimal(4209)
    assert changes[0].percentage_change == Decimal("47.9")

    assert changes[1].metric == "Adjusted operating income"
    assert changes[1].absolute_change == Decimal(1712)
    assert changes[1].percentage_change == Decimal("17.5")


def test_dataset_rejects_unknown_period():
    dataset = _build_dataset()

    with pytest.raises(
        ValueError,
        match="Expected exactly one fact set for period",
    ):
        dataset.get_fact(
            metric_id="net_operating_income",
            period="Q3 2026",
        )


def test_compare_metrics_rejects_duplicate_metric_ids():
    dataset = _build_dataset()

    with pytest.raises(
        ValueError,
        match="metric_ids must be unique",
    ):
        dataset.compare_metrics(
            metric_ids=(
                "net_operating_income",
                "net_operating_income",
            ),
            from_period="Q1 2026",
            to_period="Q2 2026",
        )