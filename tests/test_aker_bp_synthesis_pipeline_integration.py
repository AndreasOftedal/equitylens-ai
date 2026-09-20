import json

import pytest

from equitylens.analysis_pipeline import PeriodSource
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
    SynthesisLLMResponse,
)
from equitylens.synthesis_pipeline import (
    run_synthesis,
)
from equitylens.synthesis_prompt import (
    SynthesisPrompt,
)

pytestmark = pytest.mark.integration


METRIC_IDS = (
    "net_income",
    "basic_earnings_per_share",
    "operating_cash_flow",
    "total_equity_production",
)


class FakeGenerator:
    def __init__(
        self,
        raw_text: str,
    ) -> None:
        self.raw_text = raw_text
        self.prompts: list[
            SynthesisPrompt
        ] = []

    def generate(
        self,
        prompt: SynthesisPrompt,
    ) -> SynthesisLLMResponse:
        self.prompts.append(
            prompt
        )

        return SynthesisLLMResponse(
            raw_text=self.raw_text,
            model="test-model",
        )


@pytest.fixture(scope="module")
def synthesis_input():
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


def _valid_aker_bp_response() -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "title": (
                "Aker BP Q2 2026 Research Summary"
            ),
            "claims": [
                {
                    "claim_id": (
                        "production-guidance"
                    ),
                    "claim_type": (
                        "guidance_update"
                    ),
                    "text": (
                        "FY 2026 production guidance "
                        "increased from 370-400 mboepd "
                        "to 380-400 mboepd."
                    ),
                    "metric_id": (
                        "production_guidance"
                    ),
                    "target_period": "FY 2026",
                    "source_fact_ids": [],
                    "evidence_sentence_ids": [],
                },
                {
                    "claim_id": (
                        "capex-guidance"
                    ),
                    "claim_type": (
                        "guidance_update"
                    ),
                    "text": (
                        "FY 2026 capex guidance "
                        "increased from USD "
                        "6.2-6.7 billion to USD "
                        "6.8-7.2 billion."
                    ),
                    "metric_id": (
                        "capex_guidance"
                    ),
                    "target_period": "FY 2026",
                    "source_fact_ids": [],
                    "evidence_sentence_ids": [],
                },
            ],
            "limitations": [
                (
                    "Validated direct management "
                    "explanations were unavailable "
                    "for the assessed quarter-on-"
                    "quarter operating cash flow "
                    "and production changes."
                ),
            ],
        }
    )


def test_real_aker_bp_research_runs_through_guarded_synthesis(
    synthesis_input,
):
    generator = FakeGenerator(
        _valid_aker_bp_response()
    )

    result = run_synthesis(
        synthesis_input,
        generator,
        max_attempts=1,
    )

    assert result.model == "test-model"
    assert result.attempts == 1
    assert result.failures == ()

    assert (
        result.draft.title
        == "Aker BP Q2 2026 Research Summary"
    )

    claims_by_metric = {
        claim.metric_id: claim
        for claim in result.draft.claims
    }

    assert set(claims_by_metric) == {
        "production_guidance",
        "capex_guidance",
    }

    production_claim = claims_by_metric[
        "production_guidance"
    ]

    assert (
        production_claim.claim_type
        == "guidance_update"
    )

    assert (
        production_claim.target_period
        == "FY 2026"
    )

    assert (
        "370-400"
        in production_claim.text
    )

    assert (
        "380-400"
        in production_claim.text
    )

    capex_claim = claims_by_metric[
        "capex_guidance"
    ]

    assert (
        capex_claim.claim_type
        == "guidance_update"
    )

    assert (
        capex_claim.target_period
        == "FY 2026"
    )

    assert "6.2-6.7" in capex_claim.text
    assert "6.8-7.2" in capex_claim.text


def test_real_aker_bp_range_guidance_is_present_in_guarded_prompt(
    synthesis_input,
):
    generator = FakeGenerator(
        _valid_aker_bp_response()
    )

    run_synthesis(
        synthesis_input,
        generator,
        max_attempts=1,
    )

    assert len(
        generator.prompts
    ) == 1

    prompt = generator.prompts[0]

    assert (
        '"numeric_lower_bound": "370"'
        in prompt.user_message
    )

    assert (
        '"numeric_upper_bound": "400"'
        in prompt.user_message
    )

    assert (
        '"numeric_lower_bound": "380"'
        in prompt.user_message
    )

    assert (
        '"numeric_lower_bound": "6.2"'
        in prompt.user_message
    )

    assert (
        '"numeric_upper_bound": "6.7"'
        in prompt.user_message
    )

    assert (
        '"numeric_lower_bound": "6.8"'
        in prompt.user_message
    )

    assert (
        '"numeric_upper_bound": "7.2"'
        in prompt.user_message
    )


def test_real_aker_bp_synthesis_preserves_conservative_evidence_boundary(
    synthesis_input,
):
    metrics_by_id = {
        metric.metric_id: metric
        for metric in synthesis_input.metrics
    }

    assert (
        metrics_by_id[
            "operating_cash_flow"
        ].evidence_availability
        == "unavailable"
    )

    assert (
        metrics_by_id[
            "total_equity_production"
        ].evidence_availability
        == "unavailable"
    )

    assert (
        metrics_by_id[
            "operating_cash_flow"
        ].direct_explanations
        == ()
    )

    assert (
        metrics_by_id[
            "total_equity_production"
        ].direct_explanations
        == ()
    )