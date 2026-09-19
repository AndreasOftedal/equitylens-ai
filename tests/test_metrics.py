import pytest

from equitylens.metrics import (
    ADJUSTED_OPERATING_INCOME,
    CORE_FINANCIAL_METRICS,
    METRIC_REGISTRY,
    get_metric_definition,
)


def test_core_metric_registry_has_unique_metric_ids():
    metric_ids = [
        metric.metric_id
        for metric in CORE_FINANCIAL_METRICS
    ]

    assert len(metric_ids) == len(set(metric_ids))


def test_registry_contains_all_core_metrics():
    assert set(METRIC_REGISTRY) == {
        "net_operating_income",
        "net_income",
        "adjusted_operating_income",
        "adjusted_net_income",
    }


def test_adjusted_operating_income_supports_source_label_variants():
    assert ADJUSTED_OPERATING_INCOME.canonical_name == (
        "Adjusted operating income"
    )

    assert ADJUSTED_OPERATING_INCOME.source_labels == (
        "Adjusted operating income*",
        "Adjusted operating income/(loss)*",
    )

    assert ADJUSTED_OPERATING_INCOME.unit == "USD million"
    assert ADJUSTED_OPERATING_INCOME.category == "profitability"


def test_get_metric_definition_returns_registered_metric():
    metric = get_metric_definition(
        "adjusted_operating_income"
    )

    assert metric is ADJUSTED_OPERATING_INCOME


def test_get_metric_definition_rejects_unknown_metric():
    with pytest.raises(
        ValueError,
        match="Unknown metric_id",
    ):
        get_metric_definition("does_not_exist")