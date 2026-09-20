from dotenv import load_dotenv

from equitylens.analysis_pipeline import (
    PeriodSource,
)
from equitylens.documents import (
    AKER_BP_Q1_2026,
    AKER_BP_Q2_2026,
)
from equitylens.research_pipeline import (
    build_aker_bp_research_result,
)
from equitylens.synthesis_input import (
    build_synthesis_input,
)
from equitylens.synthesis_llm import (
    OpenAISynthesisClient,
)
from equitylens.synthesis_pipeline import (
    run_synthesis,
)

METRIC_IDS = (
    "net_income",
    "basic_earnings_per_share",
    "operating_cash_flow",
    "total_equity_production",
)


def build_aker_bp_synthesis_input():
    research_result = (
        build_aker_bp_research_result(
            previous_source=PeriodSource(
                document=AKER_BP_Q1_2026,
                page_number=3,
            ),
            current_source=PeriodSource(
                document=AKER_BP_Q2_2026,
                page_number=3,
            ),
            company="Aker BP ASA",
            ticker="AKRBP",
            metric_ids=METRIC_IDS,
        )
    )

    return build_synthesis_input(
        research_result
    )


def validate_live_result(
    result,
) -> None:
    claims = result.draft.claims

    financial_claims = tuple(
        claim
        for claim in claims
        if (
            claim.claim_type
            == "financial_observation"
        )
    )

    if not financial_claims:
        raise AssertionError(
            "Live synthesis returned no "
            "financial observations."
        )

    forbidden_claim_types = {
        "management_explanation",
        "consistency_observation",
    }

    forbidden_claims = tuple(
        claim
        for claim in claims
        if claim.claim_type
        in forbidden_claim_types
    )

    if forbidden_claims:
        raise AssertionError(
            "Live synthesis crossed the "
            "conservative evidence boundary: "
            f"{tuple(
                claim.claim_type
                for claim in forbidden_claims
            )}"
        )

    guidance_claims = {
        claim.metric_id: claim
        for claim in claims
        if (
            claim.claim_type
            == "guidance_update"
        )
    }

    required_guidance = {
        "production_guidance",
        "capex_guidance",
    }

    missing_guidance = (
        required_guidance
        - set(guidance_claims)
    )

    if missing_guidance:
        raise AssertionError(
            "Live synthesis omitted supported "
            "changed guidance: "
            f"{sorted(missing_guidance)}"
        )

    production = guidance_claims[
        "production_guidance"
    ]

    if production.target_period != "FY 2026":
        raise AssertionError(
            "Production guidance used the "
            "wrong target period."
        )

    production_numbers = (
        "370",
        "400",
        "380",
    )

    if not all(
        number in production.text
        for number in production_numbers
    ):
        raise AssertionError(
            "Production guidance claim did not "
            "preserve the supported range values."
        )

    capex = guidance_claims[
        "capex_guidance"
    ]

    if capex.target_period != "FY 2026":
        raise AssertionError(
            "Capex guidance used the "
            "wrong target period."
        )

    capex_numbers = (
        "6.2",
        "6.7",
        "6.8",
        "7.2",
    )

    if not all(
        number in capex.text
        for number in capex_numbers
    ):
        raise AssertionError(
            "Capex guidance claim did not "
            "preserve the supported range values."
        )


def main() -> None:
    load_dotenv()

    synthesis_input = (
        build_aker_bp_synthesis_input()
    )

    client = OpenAISynthesisClient()

    result = run_synthesis(
        synthesis_input=synthesis_input,
        generator=client,
    )

    validate_live_result(
        result
    )

    print(
        "AKER BP LIVE SYNTHESIS: PASS"
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
            "\nGuardrail rejections before "
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
            "\nFirst model output passed "
            "all guardrails."
        )

    print(
        "\nAccepted claims:"
    )

    for claim in result.draft.claims:
        print(
            f"- [{claim.claim_type}] "
            f"{claim.metric_id}: "
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