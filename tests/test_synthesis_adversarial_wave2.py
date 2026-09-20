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
):
    return SimpleNamespace(
        sentence_id=sentence_id,
        text=(
            "Net operating income increased "
            "due to higher realised prices."
        ),
    )


def _metric():
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
        consistency_status="consistent",
        evidence_availability=(
            "direct_explanation"
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
):
    return SimpleNamespace(
        metric_id="share_buyback",
        target_period="FY2026",
        category="capital_distribution",
        document_id=document_id,
        page_number=2,
        section="Capital distribution",
        statement=(
            "Expected share buyback programme."
        ),
        numeric_value=value,
        unit="USD billion",
        qualifier="up to",
        qualitative_value=None,
    )


def _input():
    previous = _guidance_item(
        "q1-document",
        "1.5",
    )

    current = _guidance_item(
        "q2-document",
        "3",
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
            _metric(),
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
        title="Wave 2 adversarial synthesis",
        claims=(
            claim,
        ),
        limitations=(),
    )


def _case(
    case_id,
    description,
    claim,
    expected_outcome,
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
    )


def test_adversarial_synthesis_wave_2():
    cases = (
        _case(
            "financial-target-period",
            (
                "Historical financial observations "
                "must not contain guidance periods."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="financial_observation",
                text=(
                    "Net operating income increased "
                    "47.9% from Q1 to Q2 2026."
                ),
                metric_id="net_operating_income",
                target_period="FY2026",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
            ),
            "reject",
        ),
        _case(
            "management-target-period",
            (
                "Management explanations must not "
                "contain guidance periods."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="management_explanation",
                text=(
                    "Management attributed the "
                    "increase to higher realised "
                    "prices."
                ),
                metric_id="net_operating_income",
                target_period="FY2026",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                ),
            ),
            "reject",
        ),
        _case(
            "consistency-target-period",
            (
                "Consistency observations must not "
                "contain guidance periods."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="consistency_observation",
                text=(
                    "Management commentary is "
                    "consistent with the increase."
                ),
                metric_id="net_operating_income",
                target_period="FY2026",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                ),
            ),
            "reject",
        ),
        _case(
            "financial-narrative-citation",
            (
                "Pure financial observations must "
                "not cite narrative evidence."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="financial_observation",
                text=(
                    "Net operating income increased "
                    "47.9% from Q1 to Q2 2026."
                ),
                metric_id="net_operating_income",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                ),
            ),
            "reject",
        ),
        _case(
            "management-missing-evidence",
            (
                "Management explanations require "
                "direct evidence citations."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="management_explanation",
                text=(
                    "Management attributed the "
                    "increase to higher realised "
                    "prices."
                ),
                metric_id="net_operating_income",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
            ),
            "reject",
        ),
        _case(
            "duplicate-source-facts",
            (
                "Deterministic source fact citations "
                "must not contain duplicates."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="financial_observation",
                text=(
                    "Net operating income increased "
                    "47.9% from Q1 to Q2 2026."
                ),
                metric_id="net_operating_income",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                    "fact-q2",
                ),
            ),
            "reject",
        ),
        _case(
            "unknown-financial-metric",
            (
                "Claims must not reference an "
                "unknown financial metric."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="financial_observation",
                text=(
                    "Invented metric increased."
                ),
                metric_id="invented_metric",
                source_fact_ids=(),
            ),
            "reject",
        ),
        _case(
            "guidance-missing-target-period",
            (
                "Guidance updates must contain a "
                "target period."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="guidance_update",
                text=(
                    "Share buyback guidance "
                    "increased."
                ),
                metric_id="share_buyback",
            ),
            "reject",
        ),
        _case(
            "unknown-guidance-item",
            (
                "Guidance claims must reference "
                "tracked guidance."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="guidance_update",
                text=(
                    "FY2027 share buyback guidance "
                    "increased."
                ),
                metric_id="share_buyback",
                target_period="FY2027",
            ),
            "reject",
        ),
        _case(
            "guidance-narrative-citation",
            (
                "Guidance updates must not use "
                "historical narrative evidence IDs."
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
                evidence_sentence_ids=(
                    "sentence-1",
                ),
            ),
            "reject",
        ),
        _case(
            "duplicate-management-evidence",
            (
                "Management evidence citations "
                "must be unique."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="management_explanation",
                text=(
                    "Management attributed the "
                    "increase to higher realised "
                    "prices."
                ),
                metric_id="net_operating_income",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                    "sentence-1",
                ),
            ),
            "reject",
        ),
        _case(
            "duplicate-consistency-evidence",
            (
                "Consistency evidence citations "
                "must also be unique."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="consistency_observation",
                text=(
                    "Management commentary is "
                    "consistent with the reported "
                    "increase."
                ),
                metric_id="net_operating_income",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                    "sentence-1",
                ),
            ),
            "reject",
        ),
        _case(
            "valid-consistency-control",
            (
                "A supported consistency claim "
                "should remain accepted."
            ),
            SynthesisClaim(
                claim_id="claim-1",
                claim_type="consistency_observation",
                text=(
                    "Management commentary is "
                    "consistent with the reported "
                    "increase."
                ),
                metric_id="net_operating_income",
                source_fact_ids=(
                    "fact-q1",
                    "fact-q2",
                ),
                evidence_sentence_ids=(
                    "sentence-1",
                ),
            ),
            "accept",
        ),
    )

    report = run_synthesis_eval(
        _input(),
        cases,
    )

    assert report.total_cases == 13
    assert report.passed_cases == 13
    assert report.failed_cases == 0
    assert report.pass_rate == 1.0