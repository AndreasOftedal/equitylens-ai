import pytest

from equitylens.metrics import (
    CORE_FINANCIAL_METRICS,
    METRIC_REGISTRY,
    get_metric_definition,
)

EXPECTED_CORE_METRIC_IDS = {
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
}


def test_core_metric_registry_has_unique_metric_ids():
    metric_ids = [
        metric.metric_id
        for metric in CORE_FINANCIAL_METRICS
    ]

    assert len(metric_ids) == len(set(metric_ids))


def test_registry_contains_all_core_metrics():
    assert set(METRIC_REGISTRY) == EXPECTED_CORE_METRIC_IDS
    assert len(METRIC_REGISTRY) == 13


def test_core_metrics_have_group_scope():
    assert {
        metric.scope
        for metric in CORE_FINANCIAL_METRICS
    } == {"group"}


def test_total_equity_production_is_group_metric():
    metric = get_metric_definition(
        "total_equity_production"
    )

    assert metric.scope == "group"


def test_adjusted_operating_income_supports_source_label_variants():
    metric = get_metric_definition(
        "adjusted_operating_income"
    )

    assert "Adjusted operating income*" in metric.source_labels
    assert (
        "Adjusted operating income/(loss)*"
        in metric.source_labels
    )


@pytest.mark.parametrize(
    ("metric_id", "source_label"),
    (
        (
            "net_income",
            "Net profit/loss",
        ),
        (
            "basic_earnings_per_share",
            "Earnings per share (EPS)",
        ),
        (
            "operating_cash_flow",
            "Cash flow from operations",
        ),
        (
            "total_equity_production",
            "Net petroleum production",
        ),
    ),
)
def test_aker_bp_source_labels_map_to_existing_metrics(
    metric_id,
    source_label,
):
    metric = get_metric_definition(
        metric_id
    )

    assert source_label in metric.source_labels


def test_get_metric_definition_returns_registered_metric():
    metric = get_metric_definition(
        "operating_cash_flow"
    )

    assert metric.metric_id == "operating_cash_flow"
    assert (
        metric.canonical_name
        == "Cash flows provided by operating activities"
    )
    assert metric.unit == "USD million"
    assert metric.category == "cash_flow"


def test_registry_contains_multiple_financial_categories():
    categories = {
        metric.category
        for metric in CORE_FINANCIAL_METRICS
    }

    assert categories == {
        "profitability",
        "cash_flow",
        "operations",
        "market",
    }


def test_eps_metrics_use_per_share_units():
    basic_eps = get_metric_definition(
        "basic_earnings_per_share"
    )

    adjusted_eps = get_metric_definition(
        "adjusted_earnings_per_share"
    )

    assert basic_eps.unit == "USD per share"
    assert adjusted_eps.unit == "USD per share"


def test_operational_metrics_use_expected_units():
    production = get_metric_definition(
        "total_equity_production"
    )

    total_power = get_metric_definition(
        "total_power_generation"
    )

    renewable_power = get_metric_definition(
        "renewable_power_generation"
    )

    assert production.unit == "mboe/day"
    assert total_power.unit == "TWh"
    assert renewable_power.unit == "TWh"


def test_get_metric_definition_rejects_unknown_metric():
    with pytest.raises(
        ValueError,
        match="Unknown metric_id",
    ):
        get_metric_definition("does_not_exist")