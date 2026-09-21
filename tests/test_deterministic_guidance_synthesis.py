import json

from equitylens.synthesis_input import (
    SynthesisGuidanceChange,
    SynthesisGuidanceItem,
    SynthesisInput,
)
from equitylens.synthesis_llm import (
    SynthesisLLMResponse,
)
from equitylens.synthesis_pipeline import (
    run_synthesis,
)


class FakeGenerator:
    def __init__(
        self,
        raw_text: str,
    ) -> None:
        self.raw_text = raw_text
        self.calls = 0

    def generate(
        self,
        prompt,
    ) -> SynthesisLLMResponse:
        self.calls += 1

        return SynthesisLLMResponse(
            raw_text=self.raw_text,
            model="test-model",
        )


def _guidance_item() -> (
    SynthesisGuidanceItem
):
    return SynthesisGuidanceItem(
        metric_id=(
            "oil_gas_production_growth"
        ),
        target_period="FY2026",
        category="formal_outlook",
        document_id="equinor-q2",
        page_number=1,
        section="Outlook",
        statement=(
            "Oil & gas production for 2026 "
            "is estimated to grow around 3% "
            "compared to 2025 level"
        ),
        numeric_value="3",
        unit="%",
        qualifier="around",
        qualitative_value=None,
    )


def _synthesis_input() -> SynthesisInput:
    previous = _guidance_item()
    current = _guidance_item()

    change = SynthesisGuidanceChange(
        metric_id=(
            "oil_gas_production_growth"
        ),
        target_period="FY2026",
        change_type="unchanged",
        previous=previous,
        current=current,
        qualifier_changed=False,
        category_changed=False,
    )

    return SynthesisInput(
        schema_version="1.0",
        company="Equinor ASA",
        ticker="EQNR",
        from_period="Q1 2026",
        to_period="Q2 2026",
        previous_document_id=(
            "equinor-q1"
        ),
        current_document_id=(
            "equinor-q2"
        ),
        metrics=(),
        guidance_changes=(
            change,
        ),
        guidance_introduced=(),
        guidance_withdrawn=(),
    )


def _model_response() -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "title": (
                "Equinor Q2 2026 "
                "Research Summary"
            ),
            "claims": [
                {
                    "claim_id": "claim-9",
                    "claim_type": (
                        "guidance_update"
                    ),
                    "text": (
                        "Oil and gas production "
                        "growth guidance was higher "
                        "at around 3%."
                    ),
                    "metric_id": (
                        "oil_gas_production_growth"
                    ),
                    "target_period": "FY2026",
                    "source_fact_ids": [],
                    "evidence_sentence_ids": [],
                }
            ],
            "limitations": [],
        }
    )


def test_model_guidance_is_rebuilt_deterministically():
    generator = FakeGenerator(
        _model_response()
    )

    result = run_synthesis(
        _synthesis_input(),
        generator,
    )

    assert generator.calls == 1
    assert result.attempts == 1
    assert result.failures == ()

    assert len(
        result.draft.claims
    ) == 1

    claim = result.draft.claims[0]

    assert claim.claim_id == "claim-9"

    assert (
        claim.claim_type
        == "guidance_update"
    )

    assert (
        claim.metric_id
        == "oil_gas_production_growth"
    )

    assert (
        claim.target_period
        == "FY2026"
    )

    assert (
        claim.text
        == (
            "Oil gas production growth "
            "guidance for FY2026 "
            "was unchanged at around 3 %."
        )
    )


def test_invalid_model_guidance_wording_cannot_survive():
    generator = FakeGenerator(
        _model_response()
    )

    result = run_synthesis(
        _synthesis_input(),
        generator,
    )

    all_text = " ".join(
        claim.text
        for claim in result.draft.claims
    ).lower()

    assert "was higher" not in all_text
    assert "was unchanged" in all_text