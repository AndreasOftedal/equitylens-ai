from types import SimpleNamespace

import pytest

from equitylens.synthesis_output import (
    SynthesisClaim,
    SynthesisDraft,
    validate_synthesis_draft,
)


def _source_fact(
    fact_id,
):
    return SimpleNamespace(
        fact_id=fact_id
    )


def _evidence(
    sentence_id,
):
    return SimpleNamespace(
        sentence_id=sentence_id
    )


def _metric(
    *,
    metric_id="net_operating_income",
    evidence_availability="direct_explanation",
    consistency_status="consistent",
):
    return SimpleNamespace(
        metric_id=metric_id,
        source_facts=(
            _source_fact("fact-q1"),
            _source_fact("fact-q2"),
        ),
        evidence_availability=(
            evidence_availability
        ),
        consistency_status=(
            consistency_status
        ),
        direct_explanations=(
            _evidence("sentence-1"),
        ),
    )


def _input(
    *,
    metric=None,
):
    if metric is None:
        metric = _metric()

    guidance = SimpleNamespace(
        metric_id="share_buyback",
        target_period="FY2026",
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


def test_valid_financial_observation_passes():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="financial_observation",
        text=(
            "Net operating income increased "
            "from Q1 to Q2."
        ),
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
    )

    validate_synthesis_draft(
        _input(),
        _draft(claim),
    )


def test_financial_observation_requires_exact_source_facts():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="financial_observation",
        text="Net operating income increased.",
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q2",
        ),
    )

    with pytest.raises(
        ValueError,
        match="exact deterministic source facts",
    ):
        validate_synthesis_draft(
            _input(),
            _draft(claim),
        )


def test_unknown_financial_metric_is_rejected():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="financial_observation",
        text="Unknown metric changed.",
        metric_id="unknown_metric",
        source_fact_ids=(),
    )

    with pytest.raises(
        ValueError,
        match="unknown financial metric",
    ):
        validate_synthesis_draft(
            _input(),
            _draft(claim),
        )


def test_valid_management_explanation_passes():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="management_explanation",
        text=(
            "Management attributed the increase "
            "to the cited driver."
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

    validate_synthesis_draft(
        _input(),
        _draft(claim),
    )


def test_management_explanation_requires_direct_evidence():
    metric = _metric(
        evidence_availability=(
            "aligned_context_only"
        )
    )

    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="management_explanation",
        text="Management explained the change.",
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
        match=(
            "no validated direct management "
            "explanation"
        ),
    ):
        validate_synthesis_draft(
            _input(metric=metric),
            _draft(claim),
        )


def test_aligned_or_unknown_sentence_cannot_support_explanation():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="management_explanation",
        text="Management explained the change.",
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
        evidence_sentence_ids=(
            "context-sentence",
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "unsupported evidence sentence IDs"
        ),
    ):
        validate_synthesis_draft(
            _input(),
            _draft(claim),
        )


def test_consistency_claim_requires_supported_status():
    metric = _metric(
        consistency_status=(
            "insufficient_evidence"
        )
    )

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

    with pytest.raises(
        ValueError,
        match=(
            "does not support a consistency "
            "conclusion"
        ),
    ):
        validate_synthesis_draft(
            _input(metric=metric),
            _draft(claim),
        )


def test_valid_consistency_claim_passes():
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

    validate_synthesis_draft(
        _input(),
        _draft(claim),
    )


def test_valid_guidance_update_passes():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="guidance_update",
        text=(
            "Expected full-year share buyback "
            "guidance increased."
        ),
        metric_id="share_buyback",
        target_period="FY2026",
    )

    validate_synthesis_draft(
        _input(),
        _draft(claim),
    )


def test_unknown_guidance_item_is_rejected():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="guidance_update",
        text="Unknown guidance changed.",
        metric_id="unknown_guidance",
        target_period="FY2026",
    )

    with pytest.raises(
        ValueError,
        match="unknown guidance item",
    ):
        validate_synthesis_draft(
            _input(),
            _draft(claim),
        )


def test_duplicate_claim_ids_are_rejected():
    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="financial_observation",
        text="Net operating income increased.",
        metric_id="net_operating_income",
        source_fact_ids=(
            "fact-q1",
            "fact-q2",
        ),
    )

    draft = SynthesisDraft(
        schema_version="1.0",
        title="Equinor Q2 2026 review",
        claims=(
            claim,
            claim,
        ),
        limitations=(),
    )

    with pytest.raises(
        ValueError,
        match="claim_ids must be unique",
    ):
        validate_synthesis_draft(
            _input(),
            draft,
        )