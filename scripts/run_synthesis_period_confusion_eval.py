from dotenv import load_dotenv

from equitylens.synthesis_input import (
    SynthesisInput,
    SynthesisMetric,
    SynthesisNarrativeEvidence,
    SynthesisSourceFact,
    SynthesisSourceRef,
)
from equitylens.synthesis_llm import OpenAISynthesisClient
from equitylens.synthesis_pipeline import run_synthesis

YOY_SOURCE_TEXT = (
    "Compared with the second quarter of 2025, "
    "net operating income decreased due to lower "
    "gas prices and reduced production."
)


def _source_fact(
    *,
    fact_id: str,
    period: str,
    value: str,
) -> SynthesisSourceFact:
    return SynthesisSourceFact(
        fact_id=fact_id,
        metric_id="net_operating_income",
        period=period,
        value=value,
        unit="USD million",
        source=SynthesisSourceRef(
            document_id=f"equinor-{period}",
            page_number=5,
            table_number=1,
            row_label="Net operating income",
            column_label=period,
        ),
    )


def build_period_confusion_input() -> SynthesisInput:
    metric = SynthesisMetric(
        metric_id="net_operating_income",
        from_period="Q1 2026",
        to_period="Q2 2026",
        from_value="8784",
        to_value="12993",
        absolute_change="4209",
        percentage_change="47.9",
        unit="USD million",
        comparison_type="qoq",
        financial_direction="increase",
        consistency_status="insufficient_evidence",
        consistency_reason=(
            "Available narrative evidence uses a "
            "different comparison period and cannot "
            "support a QoQ consistency conclusion."
        ),
        evidence_availability="aligned_context_only",
        source_facts=(
            _source_fact(
                fact_id="fact-q1",
                period="Q1 2026",
                value="8784",
            ),
            _source_fact(
                fact_id="fact-q2",
                period="Q2 2026",
                value="12993",
            ),
        ),
        direct_explanations=(),
        aligned_context=(
            SynthesisNarrativeEvidence(
                role="aligned_context",
                sentence_id="yoy-context-1",
                document_id="equinor-q2-2026",
                page_number=5,
                text=YOY_SOURCE_TEXT,
                page_start_char=200,
                page_end_char=(
                    200
                    + len(YOY_SOURCE_TEXT)
                ),
                section_context=(
                    "Financial review"
                ),
            ),
        ),
    )

    return SynthesisInput(
        schema_version="1.0",
        company="Equinor ASA",
        ticker="EQNR",
        from_period="Q1 2026",
        to_period="Q2 2026",
        previous_document_id="equinor-q1-2026",
        current_document_id="equinor-q2-2026",
        metrics=(
            metric,
        ),
        guidance_changes=(),
        guidance_introduced=(),
        guidance_withdrawn=(),
    )


def validate_period_confusion_result(
    result,
) -> None:
    forbidden_claim_types = {
        "management_explanation",
        "consistency_observation",
    }

    unsupported_claims = tuple(
        claim.claim_type
        for claim in result.draft.claims
        if claim.claim_type
        in forbidden_claim_types
    )

    if unsupported_claims:
        raise AssertionError(
            "YoY narrative evidence was promoted "
            "into an unsupported QoQ claim: "
            f"{unsupported_claims}"
        )

    financial_claims = tuple(
        claim
        for claim in result.draft.claims
        if claim.claim_type
        == "financial_observation"
    )

    if not financial_claims:
        raise AssertionError(
            "No supported financial observation "
            "was returned."
        )

    combined_financial_text = " ".join(
        claim.text.lower()
        for claim in financial_claims
    )

    if "decreased" in combined_financial_text:
        raise AssertionError(
            "The accepted QoQ financial observation "
            "reversed the deterministic direction."
        )

    forbidden_driver_fragments = (
        "lower gas prices",
        "reduced production",
    )

    leaked_drivers = tuple(
        fragment
        for fragment in forbidden_driver_fragments
        if fragment
        in combined_financial_text
    )

    if leaked_drivers:
        raise AssertionError(
            "YoY drivers leaked into the accepted "
            "QoQ financial observation: "
            f"{leaked_drivers}"
        )


def main() -> None:
    load_dotenv()

    synthesis_input = (
        build_period_confusion_input()
    )

    client = OpenAISynthesisClient()

    result = run_synthesis(
        synthesis_input=synthesis_input,
        generator=client,
    )

    validate_period_confusion_result(
        result
    )

    print(
        "PERIOD CONFUSION EVAL: PASS"
    )
    print(
        f"Model: {result.model}"
    )
    print(
        "Synthesis attempts: "
        f"{result.attempts}"
    )

    if result.failures:
        print(
            "Guardrail rejections before "
            "final acceptance:"
        )

        for failure in result.failures:
            print(
                f"- attempt {failure.attempt}: "
                f"{failure.error_type}: "
                f"{failure.error_message}"
            )
    else:
        print(
            "First model output passed all "
            "guardrails."
        )

    print(
        "\nAccepted claims:"
    )

    for claim in result.draft.claims:
        print(
            f"- {claim.claim_type}: "
            f"{claim.text}"
        )

    print(
        "\nLimitations:"
    )

    for limitation in (
        result.draft.limitations
    ):
        print(
            f"- {limitation}"
        )


if __name__ == "__main__":
    main()