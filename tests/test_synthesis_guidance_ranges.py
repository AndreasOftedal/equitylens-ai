from decimal import Decimal
from types import SimpleNamespace

from equitylens.synthesis_input import (
    _build_guidance_item,
)
from equitylens.synthesis_output import (
    SynthesisClaim,
    SynthesisDraft,
)
from equitylens.synthesis_semantics import (
    validate_synthesis_semantics,
)


def _range_guidance_item(
    *,
    document_id,
    lower_bound,
    upper_bound,
    statement,
):
    return SimpleNamespace(
        metric_id="production_guidance",
        target_period="FY 2026",
        category="operational",
        document_id=document_id,
        page_number=16,
        section="Outlook",
        statement=statement,
        numeric_value=None,
        numeric_lower_bound=Decimal(
            str(lower_bound)
        ),
        numeric_upper_bound=Decimal(
            str(upper_bound)
        ),
        unit="mboepd",
        qualifier="guidance range",
        qualitative_value=None,
    )


def _semantic_range_input():
    previous = SimpleNamespace(
        metric_id="production_guidance",
        target_period="FY 2026",
        category="operational",
        document_id="aker-bp-q1-2026-report",
        page_number=13,
        section="Outlook",
        statement=(
            "Production guidance was provided "
            "for the full year."
        ),
        numeric_value=None,
        numeric_lower_bound="370",
        numeric_upper_bound="400",
        unit="mboepd",
        qualifier="guidance range",
        qualitative_value=None,
    )

    current = SimpleNamespace(
        metric_id="production_guidance",
        target_period="FY 2026",
        category="operational",
        document_id="aker-bp-q2-2026-report",
        page_number=16,
        section="Outlook",
        statement=(
            "Production guidance was updated "
            "for the full year."
        ),
        numeric_value=None,
        numeric_lower_bound="380",
        numeric_upper_bound="400",
        unit="mboepd",
        qualifier="guidance range",
        qualitative_value=None,
    )

    guidance_change = SimpleNamespace(
        metric_id="production_guidance",
        target_period="FY 2026",
        change_type="increased",
        previous=previous,
        current=current,
        qualifier_changed=False,
        category_changed=False,
    )

    return SimpleNamespace(
        metrics=(),
        guidance_changes=(
            guidance_change,
        ),
        guidance_introduced=(),
        guidance_withdrawn=(),
    )


def test_synthesis_guidance_item_preserves_numeric_range():
    item = _range_guidance_item(
        document_id="aker-bp-q2-2026-report",
        lower_bound=380,
        upper_bound=400,
        statement=(
            "Production: 380-400 mboepd"
        ),
    )

    synthesis_item = _build_guidance_item(
        item
    )

    assert synthesis_item.numeric_value is None

    assert (
        synthesis_item.numeric_lower_bound
        == "380"
    )

    assert (
        synthesis_item.numeric_upper_bound
        == "400"
    )

    assert synthesis_item.unit == "mboepd"


def test_semantics_accepts_structured_guidance_range_values():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="guidance_update",
        text=(
            "FY 2026 production guidance "
            "increased from 370-400 mboepd "
            "to 380-400 mboepd."
        ),
        metric_id="production_guidance",
        target_period="FY 2026",
    )

    draft = SynthesisDraft(
        schema_version="1.0",
        title="Aker BP Q2 2026 review",
        claims=(
            claim,
        ),
        limitations=(),
    )

    validate_synthesis_semantics(
        _semantic_range_input(),
        draft,
    )