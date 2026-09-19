from decimal import Decimal

import pytest

from equitylens.guidance import (
    GuidanceItem,
    compare_guidance,
)


def _numeric_guidance(
    document_id: str,
    metric_id: str,
    value: str,
    unit: str,
    qualifier: str,
    category: str = "formal_outlook",
) -> GuidanceItem:
    return GuidanceItem(
        metric_id=metric_id,
        target_period="FY 2026",
        category=category,
        document_id=document_id,
        page_number=10,
        section="Outlook",
        statement="Guidance statement.",
        numeric_value=Decimal(value),
        unit=unit,
        qualifier=qualifier,
    )


def _qualitative_guidance(
    document_id: str,
    metric_id: str,
    value: str,
) -> GuidanceItem:
    return GuidanceItem(
        metric_id=metric_id,
        target_period="FY 2026",
        category="formal_outlook",
        document_id=document_id,
        page_number=10,
        section="Outlook",
        statement="Guidance statement.",
        qualitative_value=value,
        qualifier="ambition",
    )


def test_unchanged_capex_guidance():
    q1 = _numeric_guidance(
        document_id="q1",
        metric_id="organic_capex",
        value="13",
        unit="USD billion",
        qualifier="around",
    )

    q2 = _numeric_guidance(
        document_id="q2",
        metric_id="organic_capex",
        value="13",
        unit="USD billion",
        qualifier="around",
    )

    change = compare_guidance(
        q1,
        q2,
    )

    assert change.change_type == "unchanged"
    assert change.qualifier_changed is False


def test_unchanged_production_growth_guidance():
    q1 = _numeric_guidance(
        document_id="q1",
        metric_id="oil_gas_production_growth",
        value="3",
        unit="percent",
        qualifier="around",
    )

    q2 = _numeric_guidance(
        document_id="q2",
        metric_id="oil_gas_production_growth",
        value="3",
        unit="percent",
        qualifier="around",
    )

    assert (
        compare_guidance(
            q1,
            q2,
        ).change_type
        == "unchanged"
    )


def test_unchanged_maintenance_guidance():
    q1 = _numeric_guidance(
        document_id="q1",
        metric_id="maintenance_production_impact",
        value="35",
        unit="mboe per day",
        qualifier="around",
    )

    q2 = _numeric_guidance(
        document_id="q2",
        metric_id="maintenance_production_impact",
        value="35",
        unit="mboe per day",
        qualifier="around",
    )

    assert (
        compare_guidance(
            q1,
            q2,
        ).change_type
        == "unchanged"
    )


def test_unchanged_qualitative_guidance():
    q1 = _qualitative_guidance(
        document_id="q1",
        metric_id="unit_production_cost_position",
        value="top quartile of peer group",
    )

    q2 = _qualitative_guidance(
        document_id="q2",
        metric_id="unit_production_cost_position",
        value="top quartile of peer group",
    )

    assert (
        compare_guidance(
            q1,
            q2,
        ).change_type
        == "unchanged"
    )


def test_numeric_guidance_increase_is_detected():
    q1 = _numeric_guidance(
        document_id="q1",
        metric_id="share_buyback",
        value="1.5",
        unit="USD billion",
        qualifier="up to",
        category="capital_distribution",
    )

    q2 = _numeric_guidance(
        document_id="q2",
        metric_id="share_buyback",
        value="3",
        unit="USD billion",
        qualifier="expected",
        category="capital_distribution",
    )

    change = compare_guidance(
        q1,
        q2,
    )

    assert change.change_type == "increased"
    assert change.qualifier_changed is True
    assert change.category_changed is False


def test_numeric_guidance_decrease_is_detected():
    previous = _numeric_guidance(
        document_id="q1",
        metric_id="example_metric",
        value="10",
        unit="USD billion",
        qualifier="around",
    )

    current = _numeric_guidance(
        document_id="q2",
        metric_id="example_metric",
        value="8",
        unit="USD billion",
        qualifier="around",
    )

    assert (
        compare_guidance(
            previous,
            current,
        ).change_type
        == "decreased"
    )


def test_qualifier_change_is_material():
    previous = _numeric_guidance(
        document_id="q1",
        metric_id="example_metric",
        value="10",
        unit="USD billion",
        qualifier="around",
    )

    current = _numeric_guidance(
        document_id="q2",
        metric_id="example_metric",
        value="10",
        unit="USD billion",
        qualifier="up to",
    )

    change = compare_guidance(
        previous,
        current,
    )

    assert change.change_type == "changed"
    assert change.qualifier_changed is True


def test_qualitative_change_is_detected():
    previous = _qualitative_guidance(
        document_id="q1",
        metric_id="cost_position",
        value="top quartile",
    )

    current = _qualitative_guidance(
        document_id="q2",
        metric_id="cost_position",
        value="top half",
    )

    assert (
        compare_guidance(
            previous,
            current,
        ).change_type
        == "changed"
    )


def test_mismatched_metrics_are_rejected():
    previous = _numeric_guidance(
        document_id="q1",
        metric_id="capex",
        value="13",
        unit="USD billion",
        qualifier="around",
    )

    current = _numeric_guidance(
        document_id="q2",
        metric_id="production",
        value="3",
        unit="percent",
        qualifier="around",
    )

    with pytest.raises(
        ValueError,
        match="metric_ids must match",
    ):
        compare_guidance(
            previous,
            current,
        )


def test_mismatched_target_periods_are_rejected():
    previous = _numeric_guidance(
        document_id="q1",
        metric_id="capex",
        value="13",
        unit="USD billion",
        qualifier="around",
    )

    current = GuidanceItem(
        metric_id="capex",
        target_period="FY 2027",
        category="formal_outlook",
        document_id="q2",
        page_number=10,
        section="Outlook",
        statement="Guidance statement.",
        numeric_value=Decimal(13),
        unit="USD billion",
        qualifier="around",
    )

    with pytest.raises(
        ValueError,
        match="target periods must match",
    ):
        compare_guidance(
            previous,
            current,
        )


def test_numeric_unit_mismatch_is_rejected():
    previous = _numeric_guidance(
        document_id="q1",
        metric_id="capex",
        value="13",
        unit="USD billion",
        qualifier="around",
    )

    current = _numeric_guidance(
        document_id="q2",
        metric_id="capex",
        value="13",
        unit="EUR billion",
        qualifier="around",
    )

    with pytest.raises(
        ValueError,
        match="units must match",
    ):
        compare_guidance(
            previous,
            current,
        )


def test_guidance_requires_exactly_one_value_type():
    with pytest.raises(
        ValueError,
        match="exactly one numeric or qualitative value",
    ):
        GuidanceItem(
            metric_id="capex",
            target_period="FY 2026",
            category="formal_outlook",
            document_id="q1",
            page_number=10,
            section="Outlook",
            statement="Guidance statement.",
        )