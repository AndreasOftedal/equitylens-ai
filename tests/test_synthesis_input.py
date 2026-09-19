import json
from decimal import Decimal
from types import SimpleNamespace

import pytest

from equitylens.synthesis_input import (
    build_synthesis_input,
)


def _source_fact(
    fact_id,
    period,
    value,
    page_number,
):
    return SimpleNamespace(
        fact_id=fact_id,
        metric="net_operating_income",
        period=period,
        value=Decimal(value),
        unit="USD million",
        evidence=SimpleNamespace(
            document_id=f"{period}-document",
            page_number=page_number,
            table_number=1,
            row_label="Net operating income",
            column_label=period,
        ),
    )


def _sentence(
    *,
    sentence_id,
    text,
    page_number,
):
    return SimpleNamespace(
        sentence_id=sentence_id,
        document_id="q2-document",
        page_number=page_number,
        text=text,
        page_start_char=100,
        page_end_char=180,
        section_context="Financial review",
    )


def _assessed_evidence(
    sentence,
):
    return SimpleNamespace(
        sentence=sentence
    )


def _guidance_item(
    *,
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
        numeric_value=Decimal(value),
        unit="USD billion",
        qualifier="up to",
        qualitative_value=None,
    )


def _research_result(
    *,
    evidence_assessment=None,
):
    previous_fact = _source_fact(
        fact_id="fact-q1",
        period="Q1 2026",
        value="8784",
        page_number=5,
    )

    current_fact = _source_fact(
        fact_id="fact-q2",
        period="Q2 2026",
        value="12993",
        page_number=5,
    )

    metric_result = SimpleNamespace(
        metric_id="net_operating_income",
        change=SimpleNamespace(
            from_period="Q1 2026",
            to_period="Q2 2026",
            from_value=Decimal(8784),
            to_value=Decimal(12993),
            absolute_change=Decimal(4209),
            percentage_change=Decimal("47.9"),
            unit="USD million",
            comparison_type="qoq",
        ),
        audit_trail=SimpleNamespace(
            source_facts=(
                previous_fact,
                current_fact,
            )
        ),
        evidence_assessment=(
            evidence_assessment
        ),
    )

    analyst_report = SimpleNamespace(
        company="Equinor ASA",
        ticker="EQNR",
        from_period="Q1 2026",
        to_period="Q2 2026",
        metric_results=(
            metric_result,
        ),
    )

    consistency = SimpleNamespace(
        metric_id="net_operating_income",
        status="insufficient_evidence",
        financial_direction="increase",
        comparison_type="qoq",
        narrative_directions=(),
        reason=(
            "No validated direct management "
            "explanation is available."
        ),
    )

    previous_guidance = _guidance_item(
        document_id="q1-document",
        value="1.5",
        statement=(
            "The expected share buy-back "
            "programme for 2026 is up to "
            "USD 1.5 billion."
        ),
    )

    current_guidance = _guidance_item(
        document_id="q2-document",
        value="3",
        statement=(
            "This brings the total expected "
            "programme for 2026 to up to "
            "USD 3 billion."
        ),
    )

    guidance_change = SimpleNamespace(
        metric_id="share_buyback",
        target_period="FY2026",
        change_type="increased",
        previous=previous_guidance,
        current=current_guidance,
        qualifier_changed=False,
        category_changed=False,
    )

    guidance_report = SimpleNamespace(
        previous_document_id="q1-document",
        current_document_id="q2-document",
        changes=(
            guidance_change,
        ),
        introduced=(),
        withdrawn=(),
    )

    return SimpleNamespace(
        analyst_report=analyst_report,
        guidance_report=guidance_report,
        consistency_assessments=(
            consistency,
        ),
    )


def test_builds_root_research_metadata():
    synthesis = build_synthesis_input(
        _research_result()
    )

    assert synthesis.schema_version == "1.0"
    assert synthesis.company == "Equinor ASA"
    assert synthesis.ticker == "EQNR"
    assert synthesis.from_period == "Q1 2026"
    assert synthesis.to_period == "Q2 2026"

    assert (
        synthesis.previous_document_id
        == "q1-document"
    )

    assert (
        synthesis.current_document_id
        == "q2-document"
    )


def test_financial_values_remain_exact_strings():
    synthesis = build_synthesis_input(
        _research_result()
    )

    metric = synthesis.metrics[0]

    assert metric.from_value == "8784"
    assert metric.to_value == "12993"
    assert metric.absolute_change == "4209"
    assert metric.percentage_change == "47.9"
    assert metric.unit == "USD million"


def test_financial_source_provenance_is_preserved():
    synthesis = build_synthesis_input(
        _research_result()
    )

    source_fact = (
        synthesis.metrics[0]
        .source_facts[0]
    )

    assert source_fact.fact_id == "fact-q1"
    assert source_fact.period == "Q1 2026"
    assert source_fact.source.page_number == 5
    assert source_fact.source.table_number == 1

    assert (
        source_fact.source.row_label
        == "Net operating income"
    )

    assert (
        source_fact.source.column_label
        == "Q1 2026"
    )


def test_missing_evidence_is_explicitly_not_evaluated():
    synthesis = build_synthesis_input(
        _research_result()
    )

    metric = synthesis.metrics[0]

    assert (
        metric.evidence_availability
        == "not_evaluated"
    )

    assert metric.direct_explanations == ()
    assert metric.aligned_context == ()


def test_narrative_evidence_roles_and_provenance_are_preserved():
    direct_sentence = _sentence(
        sentence_id="direct-1",
        text=(
            "Net operating income increased "
            "compared to the prior quarter."
        ),
        page_number=5,
    )

    context_sentence = _sentence(
        sentence_id="context-1",
        text=(
            "Market conditions remained volatile "
            "during the quarter."
        ),
        page_number=6,
    )

    evidence_assessment = SimpleNamespace(
        availability="direct_explanation",
        direct_explanations=(
            _assessed_evidence(
                direct_sentence
            ),
        ),
        aligned_context=(
            _assessed_evidence(
                context_sentence
            ),
        ),
    )

    synthesis = build_synthesis_input(
        _research_result(
            evidence_assessment=(
                evidence_assessment
            ),
        )
    )

    metric = synthesis.metrics[0]

    assert (
        metric.evidence_availability
        == "direct_explanation"
    )

    direct = metric.direct_explanations[0]
    context = metric.aligned_context[0]

    assert direct.role == "direct_explanation"
    assert direct.sentence_id == "direct-1"
    assert direct.document_id == "q2-document"
    assert direct.page_number == 5

    assert context.role == "aligned_context"
    assert context.sentence_id == "context-1"
    assert context.page_number == 6


def test_guidance_change_and_original_statements_are_preserved():
    synthesis = build_synthesis_input(
        _research_result()
    )

    guidance = (
        synthesis.guidance_changes[0]
    )

    assert guidance.metric_id == "share_buyback"
    assert guidance.change_type == "increased"

    assert (
        guidance.previous.numeric_value
        == "1.5"
    )

    assert (
        guidance.current.numeric_value
        == "3"
    )

    assert (
        guidance.previous.document_id
        == "q1-document"
    )

    assert (
        guidance.current.document_id
        == "q2-document"
    )

    assert "1.5" in (
        guidance.previous.statement
    )

    assert "3 billion" in (
        guidance.current.statement
    )


def test_payload_is_json_serializable_without_decimal_conversion():
    synthesis = build_synthesis_input(
        _research_result()
    )

    payload = synthesis.to_dict()

    serialized = json.dumps(
        payload
    )

    assert '"4209"' in serialized
    assert '"47.9"' in serialized
    assert '"1.5"' in serialized


def test_missing_consistency_metric_is_rejected():
    research_result = (
        _research_result()
    )

    research_result = SimpleNamespace(
        analyst_report=(
            research_result.analyst_report
        ),
        guidance_report=(
            research_result.guidance_report
        ),
        consistency_assessments=(),
    )

    with pytest.raises(
        ValueError,
        match=(
            "must match analyst report "
            "metrics exactly"
        ),
    ):
        build_synthesis_input(
            research_result
        )


def test_duplicate_consistency_metric_is_rejected():
    research_result = (
        _research_result()
    )

    assessment = (
        research_result
        .consistency_assessments[0]
    )

    research_result = SimpleNamespace(
        analyst_report=(
            research_result.analyst_report
        ),
        guidance_report=(
            research_result.guidance_report
        ),
        consistency_assessments=(
            assessment,
            assessment,
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "duplicate metric_ids"
        ),
    ):
        build_synthesis_input(
            research_result
        )