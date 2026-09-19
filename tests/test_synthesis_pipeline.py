import json

import pytest

from equitylens.synthesis_input import SynthesisInput
from equitylens.synthesis_llm import SynthesisLLMResponse
from equitylens.synthesis_pipeline import run_synthesis
from equitylens.synthesis_prompt import SynthesisPrompt


class FakeGenerator:
    def __init__(
        self,
        raw_text: str,
        model: str = "test-model",
    ) -> None:
        self.raw_text = raw_text
        self.model = model
        self.prompts: list[SynthesisPrompt] = []

    def generate(
        self,
        prompt: SynthesisPrompt,
    ) -> SynthesisLLMResponse:
        self.prompts.append(
            prompt
        )

        return SynthesisLLMResponse(
            raw_text=self.raw_text,
            model=self.model,
        )


def _synthesis_input() -> SynthesisInput:
    return SynthesisInput(
        schema_version="1.0",
        company="Equinor ASA",
        ticker="EQNR",
        from_period="Q1 2026",
        to_period="Q2 2026",
        previous_document_id=(
            "equinor-q1-2026-financial-statements-and-review"
        ),
        current_document_id=(
            "equinor-q2-2026-financial-statements-and-review"
        ),
        metrics=(),
        guidance_changes=(),
        guidance_introduced=(),
        guidance_withdrawn=(),
    )


def _valid_response() -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "title": "Equinor Q2 2026 Research Summary",
            "claims": [],
            "limitations": [
                "No supported claims were available.",
            ],
        }
    )


def test_run_synthesis_returns_validated_draft():
    synthesis_input = _synthesis_input()

    generator = FakeGenerator(
        raw_text=_valid_response(),
        model="test-model",
    )

    result = run_synthesis(
        synthesis_input,
        generator,
    )

    assert (
        result.draft.schema_version
        == "1.0"
    )

    assert (
        result.draft.title
        == "Equinor Q2 2026 Research Summary"
    )

    assert result.draft.claims == ()

    assert result.model == "test-model"


def test_run_synthesis_builds_guarded_prompt():
    synthesis_input = _synthesis_input()

    generator = FakeGenerator(
        raw_text=_valid_response()
    )

    run_synthesis(
        synthesis_input,
        generator,
    )

    assert len(
        generator.prompts
    ) == 1

    prompt = generator.prompts[0]

    assert (
        "RESEARCH_DATA_START"
        in prompt.user_message
    )

    assert (
        "RESEARCH_DATA_END"
        in prompt.user_message
    )

    assert (
        synthesis_input.current_document_id
        in prompt.user_message
    )


def test_run_synthesis_rejects_invalid_json():
    generator = FakeGenerator(
        raw_text="not valid json"
    )

    with pytest.raises(
        ValueError,
    ):
        run_synthesis(
            _synthesis_input(),
            generator,
        )


def test_run_synthesis_calls_semantic_validator(
    monkeypatch,
):
    synthesis_input = _synthesis_input()

    generator = FakeGenerator(
        raw_text=_valid_response()
    )

    validated = {}

    def fake_validator(
        received_input,
        received_draft,
    ):
        validated["input"] = (
            received_input
        )
        validated["draft"] = (
            received_draft
        )

    monkeypatch.setattr(
        "equitylens.synthesis_pipeline."
        "validate_synthesis_semantics",
        fake_validator,
    )

    result = run_synthesis(
        synthesis_input,
        generator,
    )

    assert (
        validated["input"]
        is synthesis_input
    )

    assert (
        validated["draft"]
        is result.draft
    )


def test_run_synthesis_does_not_return_semantically_invalid_draft(
    monkeypatch,
):
    generator = FakeGenerator(
        raw_text=_valid_response()
    )

    def reject_draft(
        synthesis_input,
        draft,
    ):
        raise ValueError(
            "semantic validation failed"
        )

    monkeypatch.setattr(
        "equitylens.synthesis_pipeline."
        "validate_synthesis_semantics",
        reject_draft,
    )

    with pytest.raises(
        ValueError,
        match="semantic validation failed",
    ):
        run_synthesis(
            _synthesis_input(),
            generator,
        )