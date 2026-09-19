from dataclasses import dataclass
from typing import Literal

MetricCategory = Literal[
    "profitability",
    "cash_flow",
    "operations",
    "market",
    "capital_structure",
]


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    canonical_name: str
    source_labels: tuple[str, ...]
    unit: str
    category: MetricCategory


NET_OPERATING_INCOME = MetricDefinition(
    metric_id="net_operating_income",
    canonical_name="Net operating income",
    source_labels=(
        "Net operating income/(loss)",
    ),
    unit="USD million",
    category="profitability",
)

NET_INCOME = MetricDefinition(
    metric_id="net_income",
    canonical_name="Net income",
    source_labels=(
        "Net income/(loss)",
    ),
    unit="USD million",
    category="profitability",
)

BASIC_EARNINGS_PER_SHARE = MetricDefinition(
    metric_id="basic_earnings_per_share",
    canonical_name="Basic earnings per share",
    source_labels=(
        "Basic earnings per share (USD)",
    ),
    unit="USD per share",
    category="profitability",
)

ADJUSTED_OPERATING_INCOME = MetricDefinition(
    metric_id="adjusted_operating_income",
    canonical_name="Adjusted operating income",
    source_labels=(
        "Adjusted operating income*",
        "Adjusted operating income/(loss)*",
    ),
    unit="USD million",
    category="profitability",
)

ADJUSTED_NET_INCOME = MetricDefinition(
    metric_id="adjusted_net_income",
    canonical_name="Adjusted net income",
    source_labels=(
        "Adjusted net income*",
    ),
    unit="USD million",
    category="profitability",
)

ADJUSTED_EARNINGS_PER_SHARE = MetricDefinition(
    metric_id="adjusted_earnings_per_share",
    canonical_name="Adjusted earnings per share",
    source_labels=(
        "Adjusted earnings per share* (USD)",
    ),
    unit="USD per share",
    category="profitability",
)

OPERATING_CASH_FLOW = MetricDefinition(
    metric_id="operating_cash_flow",
    canonical_name="Cash flows provided by operating activities",
    source_labels=(
        "Cash flows provided by operating activities",
    ),
    unit="USD million",
    category="cash_flow",
)

OPERATING_CASH_FLOW_AFTER_TAX = MetricDefinition(
    metric_id="operating_cash_flow_after_tax",
    canonical_name="Cash flow from operations after taxes paid",
    source_labels=(
        "Cash flow from operations after taxes paid*",
    ),
    unit="USD million",
    category="cash_flow",
)

NET_CASH_FLOW_BEFORE_CAPITAL_DISTRIBUTION = MetricDefinition(
    metric_id="net_cash_flow_before_capital_distribution",
    canonical_name="Net cash flow before capital distribution",
    source_labels=(
        "Net cash flow before capital distribution*",
    ),
    unit="USD million",
    category="cash_flow",
)

GROUP_AVERAGE_LIQUIDS_PRICE = MetricDefinition(
    metric_id="group_average_liquids_price",
    canonical_name="Group average liquids price",
    source_labels=(
        "Group average liquids price (USD/bbl) [1]",
    ),
    unit="USD/bbl",
    category="market",
)

TOTAL_EQUITY_PRODUCTION = MetricDefinition(
    metric_id="total_equity_production",
    canonical_name="Total equity liquids and gas production",
    source_labels=(
        "Total equity liquids and gas production (mboe per day) [3]",
    ),
    unit="mboe/day",
    category="operations",
)

TOTAL_POWER_GENERATION = MetricDefinition(
    metric_id="total_power_generation",
    canonical_name="Total power generation",
    source_labels=(
        "Total power generation (TWh) Equinor share",
    ),
    unit="TWh",
    category="operations",
)

RENEWABLE_POWER_GENERATION = MetricDefinition(
    metric_id="renewable_power_generation",
    canonical_name="Renewable power generation",
    source_labels=(
        "Renewable power generation (TWh) Equinor share",
    ),
    unit="TWh",
    category="operations",
)


CORE_FINANCIAL_METRICS = (
    NET_OPERATING_INCOME,
    NET_INCOME,
    BASIC_EARNINGS_PER_SHARE,
    ADJUSTED_OPERATING_INCOME,
    ADJUSTED_NET_INCOME,
    ADJUSTED_EARNINGS_PER_SHARE,
    OPERATING_CASH_FLOW,
    OPERATING_CASH_FLOW_AFTER_TAX,
    NET_CASH_FLOW_BEFORE_CAPITAL_DISTRIBUTION,
    GROUP_AVERAGE_LIQUIDS_PRICE,
    TOTAL_EQUITY_PRODUCTION,
    TOTAL_POWER_GENERATION,
    RENEWABLE_POWER_GENERATION,
)


METRIC_REGISTRY = {
    metric.metric_id: metric
    for metric in CORE_FINANCIAL_METRICS
}


def get_metric_definition(
    metric_id: str,
) -> MetricDefinition:
    try:
        return METRIC_REGISTRY[metric_id]
    except KeyError as exc:
        raise ValueError(
            f"Unknown metric_id: {metric_id!r}."
        ) from exc