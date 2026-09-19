import pytest

from equitylens.evidence_queries import (
    EVIDENCE_QUERY_DEFINITIONS,
    get_evidence_enabled_metric_ids,
    get_evidence_query,
)
from equitylens.metrics import (
    get_metric_definition,
)


def test_cash_flow_uses_narrative_query():
    assert (
        get_evidence_query(
            "operating_cash_flow"
        )
        == "What drove cash flow?"
    )


def test_production_uses_narrative_query():
    assert (
        get_evidence_query(
            "total_equity_production"
        )
        == "What drove production?"
    )


def test_adjusted_operating_income_query():
    assert (
        get_evidence_query(
            "adjusted_operating_income"
        )
        == (
            "What drove adjusted operating income?"
        )
    )


def test_net_operating_income_query():
    assert (
        get_evidence_query(
            "net_operating_income"
        )
        == "What drove net operating income?"
    )


def test_renewable_generation_query():
    assert (
        get_evidence_query(
            "renewable_power_generation"
        )
        == (
            "What drove renewable power generation?"
        )
    )


def test_unvalidated_registered_metric_returns_none():
    assert (
        get_evidence_query(
            "net_income"
        )
        is None
    )


def test_unknown_metric_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unknown metric_id",
    ):
        get_evidence_query(
            "not_a_real_metric"
        )


def test_all_evidence_metrics_exist_in_metric_registry():
    for definition in (
        EVIDENCE_QUERY_DEFINITIONS
    ):
        metric = get_metric_definition(
            definition.metric_id
        )

        assert (
            metric.metric_id
            == definition.metric_id
        )


def test_evidence_metric_ids_are_unique():
    metric_ids = (
        get_evidence_enabled_metric_ids()
    )

    assert (
        len(metric_ids)
        == len(set(metric_ids))
    )


def test_queries_are_non_empty_questions():
    for definition in (
        EVIDENCE_QUERY_DEFINITIONS
    ):
        assert (
            definition.query.strip()
        )

        assert (
            definition.query.endswith("?")
        )