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


CORE_FINANCIAL_METRICS = (
    NET_OPERATING_INCOME,
    NET_INCOME,
    ADJUSTED_OPERATING_INCOME,
    ADJUSTED_NET_INCOME,
)


METRIC_REGISTRY = {
    metric.metric_id: metric
    for metric in CORE_FINANCIAL_METRICS
}


def get_metric_definition(metric_id: str) -> MetricDefinition:
    try:
        return METRIC_REGISTRY[metric_id]
    except KeyError as exc:
        raise ValueError(
            f"Unknown metric_id: {metric_id!r}."
        ) from exc