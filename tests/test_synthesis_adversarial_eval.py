from types import SimpleNamespace

from equitylens.synthesis_eval import (
    SynthesisEvalCase,
    run_synthesis_eval,
)
from equitylens.synthesis_output import (
    SynthesisClaim,
    SynthesisDraft,
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
    evidence_availability="direct_explanation",
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
        financial_direction="increase",
        consistency_status=(
            consistency_status
        ),
        evidence_availability=(
            evidence_availability
        ),
        source_facts=(
            _source_fact(
                "fact-q1"
            ),
            _source_fact(
                "fact-q2"
            ),
        ),
        direct_explanations=(
            _evidence(),
        ),
        aligned_context=(),
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
        change_type="increased",
        previous=previous,
        current=current,
        qualifier_changed=False,
        category_changed=False,
    )

    return SimpleNamespace(
        metrics=(
            metric,
        ),
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
        title="Adversarial synthesis",
        claims=(
            claim,
        ),
        limitations=(),
    )


def _financial_claim(
    *,
    text,
    source_fact_ids=(
        "fact-q1",
        "fact-q2",
    ),
):
    return SynthesisClaim(
        claim_id="claim-1",
        claim_type="financial_observation",
        text=text,
        metric_id="net_operating_income",
        source_fact_ids=source_fact_ids,
    )


def _case(
    case_id,
    description,
    claim,
    expected_outcome,
    synthesis_input=None,
):
    return SynthesisEvalCase(
        case_id=case_id,
        description=description,
        draft=_draft(
            claim
        ),
        expected_outcome=(
            expected_outcome
        ),
        synthesis_input=(
            synthesis_input
        ),
    )


def test_adversarial_synthesis_guardrail_benchmark():
    aligned_context_input = _input(
        metric=_metric(
            evidence_availability=(
                "aligned_context_only"
            )
        )
    )

    insufficient_evidence_input = _input(
        metric=_metric(
            consistency_status=(
                "insufficient_evidence"
            )
        )
    )

    cases = (
        _case(
            "valid-financial-control",
            (
                "A supported financial observation "
                "should remain accepted."
            ),
            _financial_claim(
                text=(
                    "Net operating income increased "
                    "47.9% from 8,784 in Q1 2026 "
                    "to 12,993 in Q2 2026."
                ),
            ),
            "accept",
        ),
        _case(
            "fabricated-number",
            (
                "Reject a financial claim containing "
                "a number absent from deterministic "
                "research data."
            ),
            _financial_claim(
                text=(
                    "Net operating income increased "
                    "60% from Q1 to Q2 2026."
                ),
            ),
            "reject",
        ),
        _case(
            "reversed-financial-direction",
            (
                "Reject a claim that reverses the "
                "deterministic financial direction."
            ),
            _financial_claim(
                text=(
                    "Net operating income decreased "
                    "47.9% from Q1 to Q2 2026."
                ),
            ),
            "reject",
        ),
        _case(
            "fabricated-source-fact",
            (
                "Reject a claim that cites an "
                "invented source fact."
            ),
            _financial_claim(
                text=(
                    "Net operating income increased "
                    "47.9% from Q1 to Q2 2026."
                ),
                source_fact_ids=(
                    "fact-q1",
                    "invented-fact",
                ),
            ),
            "reject",
        ),
        _case(
            "aligned-context-as-explanation",
            (
                "Reject management causality when "
                "only aligned context is available."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type=(
                    "management_explanation"
                ),
                text=(
                    "Management attributed the "
                    "increase to higher realised "
                    "prices."
                ),
                metric_id=(
                    "net_operating_income"
                ),
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                ),
            ),
            "reject",
            synthesis_input=(
                aligned_context_input
            ),
        ),
        _case(
            "fabricated-evidence-id",
            (
                "Reject a management explanation "
                "that cites invented narrative "
                "evidence."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type=(
                    "management_explanation"
                ),
                text=(
                    "Management attributed the "
                    "increase to higher realised "
                    "prices."
                ),
                metric_id=(
                    "net_operating_income"
                ),
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "invented-sentence",
                ),
            ),
            "reject",
        ),
        _case(
            "unsupported-consistency-conclusion",
            (
                "Reject a consistency conclusion "
                "when evidence is insufficient."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type=(
                    "consistency_observation"
                ),
                text=(
                    "Management commentary is "
                    "consistent with the reported "
                    "increase."
                ),
                metric_id=(
                    "net_operating_income"
                ),
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                ),
            ),
            "reject",
            synthesis_input=(
                insufficient_evidence_input
            ),
        ),
        _case(
            "guidance-with-historical-facts",
            (
                "Reject guidance that improperly "
                "cites historical financial facts."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="guidance_update",
                text=(
                    "FY2026 share buyback guidance "
                    "increased from USD 1.5 billion "
                    "to USD 3 billion."
                ),
                metric_id="share_buyback",
                target_period="FY2026",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
            ),
            "reject",
        ),
        _case(
            "reversed-guidance-direction",
            (
                "Reject guidance text that reverses "
                "the deterministic guidance change."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="guidance_update",
                text=(
                    "FY2026 share buyback guidance "
                    "decreased from USD 1.5 billion "
                    "to USD 3 billion."
                ),
                metric_id="share_buyback",
                target_period="FY2026",
            ),
            "reject",
        ),
        _case(
            "fabricated-guidance-number",
            (
                "Reject guidance containing a value "
                "not present in the tracked guidance."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="guidance_update",
                text=(
                    "FY2026 share buyback guidance "
                    "increased from USD 1.5 billion "
                    "to USD 4 billion."
                ),
                metric_id="share_buyback",
                target_period="FY2026",
            ),
            "reject",
        ),
    )

    report = run_synthesis_eval(
        _input(),
        cases,
    )

    assert report.total_cases == 10
    assert report.passed_cases == 10
    assert report.failed_cases == 0
    assert report.pass_rate == 1.0


def test_aligned_context_attack_uses_restricted_input():
    metric = _metric(
        evidence_availability=(
            "aligned_context_only"
        )
    )

    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type="management_explanation",
        text=(
            "Management attributed the increase "
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

    report = run_synthesis_eval(
        _input(
            metric=metric
        ),
        (
            _case(
                "aligned-context-only",
                (
                    "Aligned context must not become "
                    "a management explanation."
                ),
                claim,
                "reject",
            ),
        ),
    )

    assert report.pass_rate == 1.0

    assert (
        report.results[0].observed_outcome
        == "reject"
    )

    assert (
        "no validated direct management explanation"
        in report.results[0].error_message
    )


def test_insufficient_evidence_attack_uses_restricted_input():
    metric = _metric(
        consistency_status=(
            "insufficient_evidence"
        )
    )

    claim = SynthesisClaim(
        claim_id="claim-1",
        claim_type=(
            "consistency_observation"
        ),
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

    report = run_synthesis_eval(
        _input(
            metric=metric
        ),
        (
            _case(
                "insufficient-evidence",
                (
                    "Insufficient evidence must not "
                    "be promoted to a conclusion."
                ),
                claim,
                "reject",
            ),
        ),
    )

    assert report.pass_rate == 1.0

    assert (
        report.results[0].observed_outcome
        == "reject"
    )

    assert (
        "does not support a consistency conclusion"
        in report.results[0].error_message
    )