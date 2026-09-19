from types import SimpleNamespace

import pytest

from equitylens.synthesis_output import (
    SynthesisClaim,
    SynthesisDraft,
)
from equitylens.synthesis_semantics import (
    validate_synthesis_semantics,
)


def _source_fact(
    fact_id,
):
    return SimpleNamespace(
        fact_id=fact_id
    )


def _evidence(
    sentence_id="sentence-1",
    text=(
        "Net operating income increased "
        "due to higher realised prices."
    ),
):
    return SimpleNamespace(
        sentence_id=sentence_id,
        text=text,
    )


def _metric(
    *,
    financial_direction="increase",
    consistency_status="consistent",
):
    return SimpleNamespace(
        metric_id="net_operating_income",
        from_period="Q1 2026",
        to_period="Q2 2026",
        from_value="8784",
        to_value="12993",
        absolute_change="4209",
        percentage_change="47.9",
        unit="USD million",
        financial_direction=(
            financial_direction
        ),
        consistency_status=(
            consistency_status
        ),
        evidence_availability=(
            "direct_explanation"
        ),
        source_facts=(
            _source_fact("fact-q1"),
            _source_fact("fact-q2"),
        ),
        direct_explanations=(
            _evidence(),
        ),
    )


def _guidance_item(
    document_id,
    value,
    statement,
):
    return SimpleNamespace(
        metric_id="share_buyback",
        target_period="FY2026",
        category="capital_distribution",
        document_id=document_id,
        page_number=2,
        section="Capital distribution",
        statement=statement,
        numeric_value=value,
        unit="USD billion",
        qualifier="up to",
        qualitative_value=None,
    )


def _input(
    *,
    metric=None,
    guidance_change_type="increased",
):
    if metric is None:
        metric = _metric()

    previous = _guidance_item(
        "q1-document",
        "1.5",
        (
            "The expected share buy-back "
            "programme for 2026 is up to "
            "USD 1.5 billion."
        ),
    )

    current = _guidance_item(
        "q2-document",
        "3",
        (
            "The total expected programme "
            "for 2026 is up to USD 3 billion."
        ),
    )

    guidance = SimpleNamespace(
        metric_id="share_buyback",
        target_period="FY2026",
        change_type=(
            guidance_change_type
        ),
        previous=previous,
        current=current,
        qualifier_changed=False,
        category_changed=False,
    )

    return SimpleNamespace(
        metrics=(metric,),
        guidance_changes=(
            guidance,
        ),
        guidance_introduced=(),
        guidance_withdrawn=(),
    )


def _draft(
    claim,
):
    return SynthesisDraft(
        schema_version="1.0",
        title="Equinor Q2 2026 review",
        claims=(claim,),
        limitations=(),
    )


def _financial_claim(
    text,
):
    return SynthesisClaim(
        claim_id="claim-1",
        claim_type="financial_observation",
        text=text,
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
    )


def test_valid_financial_direction_and_numbers_pass():
    claim = _financial_claim(
        
            "Net operating income increased "
            "47.9% from 8,784 in Q1 2026 "
            "to 12,993 in Q2 2026."
        
    )

    validate_synthesis_semantics(
        _input(),
        _draft(claim),
    )


def test_wrong_financial_direction_is_rejected():
    claim = _financial_claim(
        
            "Net operating income decreased "
            "47.9% from Q1 to Q2 2026."
        
    )

    with pytest.raises(
        ValueError,
        match="deterministic direction",
    ):
        validate_synthesis_semantics(
            _input(),
            _draft(claim),
        )


def test_financial_claim_requires_explicit_direction():
    claim = _financial_claim(
        
            "Net operating income was 12,993 "
            "in Q2 2026."
        
    )

    with pytest.raises(
        ValueError,
        match="explicit supported financial direction",
    ):
        validate_synthesis_semantics(
            _input(),
            _draft(claim),
        )


def test_wrong_percentage_is_rejected():
    claim = _financial_claim(
        
            "Net operating income increased "
            "48.5% from Q1 to Q2 2026."
        
    )

    with pytest.raises(
        ValueError,
        match="unsupported numeric values",
    ):
        validate_synthesis_semantics(
            _input(),
            _draft(claim),
        )


def test_management_explanation_may_omit_direction():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="management_explanation",
        text=(
            "Management attributed the movement "
            "to higher realised prices."
        ),
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
        evidence_sentence_ids=(
            "sentence-1",
        ),
    )

    validate_synthesis_semantics(
        _input(),
        _draft(claim),
    )


def test_management_explanation_cannot_reverse_direction():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="management_explanation",
        text=(
            "Management said net operating "
            "income decreased due to higher "
            "realised prices."
        ),
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
        evidence_sentence_ids=(
            "sentence-1",
        ),
    )

    with pytest.raises(
        ValueError,
        match="deterministic direction",
    ):
        validate_synthesis_semantics(
            _input(),
            _draft(claim),
        )


def test_valid_consistency_language_passes():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="consistency_observation",
        text=(
            "Management commentary is consistent "
            "with the reported increase."
        ),
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
        evidence_sentence_ids=(
            "sentence-1",
        ),
    )

    validate_synthesis_semantics(
        _input(),
        _draft(claim),
    )


def test_consistency_language_must_match_status():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="consistency_observation",
        text=(
            "Management commentary is consistent "
            "with the reported movement."
        ),
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
        evidence_sentence_ids=(
            "sentence-1",
        ),
    )

    metric = _metric(
        consistency_status="potential_tension"
    )

    with pytest.raises(
        ValueError,
        match="potential_tension",
    ):
        validate_synthesis_semantics(
            _input(metric=metric),
            _draft(claim),
        )


def test_valid_guidance_direction_and_values_pass():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="guidance_update",
        text=(
            "FY2026 share buyback guidance "
            "increased from USD 1.5 billion "
            "to USD 3 billion."
        ),
        metric_id="share_buyback",
        target_period="FY2026",
    )

    validate_synthesis_semantics(
        _input(),
        _draft(claim),
    )


def test_wrong_guidance_direction_is_rejected():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="guidance_update",
        text=(
            "FY2026 share buyback guidance "
            "decreased from USD 1.5 billion "
            "to USD 3 billion."
        ),
        metric_id="share_buyback",
        target_period="FY2026",
    )

    with pytest.raises(
        ValueError,
        match="guidance change type",
    ):
        validate_synthesis_semantics(
            _input(),
            _draft(claim),
        )


def test_unsupported_guidance_number_is_rejected():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="guidance_update",
        text=(
            "FY2026 share buyback guidance "
            "increased from USD 1.5 billion "
            "to USD 4 billion."
        ),
        metric_id="share_buyback",
        target_period="FY2026",
    )

    with pytest.raises(
        ValueError,
        match="unsupported numeric values",
    ):
        validate_synthesis_semantics(
            _input(),
            _draft(claim),
        )