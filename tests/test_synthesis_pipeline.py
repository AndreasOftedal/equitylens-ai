import json

import pytest

from equitylens.synthesis_input import SynthesisInput
from equitylens.synthesis_llm import SynthesisLLMResponse
from equitylens.synthesis_pipeline import run_synthesis
from equitylens.synthesis_prompt import SynthesisPrompt


class FakeGenerator:
    def __init__(
        self,
        raw_texts: str | tuple[str, ...],
        model: str = "test-model",
    ) -> None:
        if isinstance(
            raw_texts,
            str,
        ):
            raw_texts = (
                raw_texts,
            )

        self.raw_texts = raw_texts
        self.model = model
        self.prompts: list[SynthesisPrompt] = []

    def generate(
        self,
        prompt: SynthesisPrompt,
    ) -> SynthesisLLMResponse:
        self.prompts.append(
            prompt
        )

        response_index = min(
            len(self.prompts) - 1,
            len(self.raw_texts) - 1,
        )

        return SynthesisLLMResponse(
            raw_text=self.raw_texts[
                response_index
            ],
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
        raw_texts=_valid_response(),
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
    assert result.attempts == 1
    assert result.failures == ()


def test_run_synthesis_builds_guarded_prompt():
    synthesis_input = _synthesis_input()

    generator = FakeGenerator(
        raw_texts=_valid_response()
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


def test_run_synthesis_retries_invalid_json_then_succeeds():
    generator = FakeGenerator(
        raw_texts=(
            "not valid json",
            _valid_response(),
        )
    )

    result = run_synthesis(
        _synthesis_input(),
        generator,
    )

    assert result.attempts == 2

    assert len(
        result.failures
    ) == 1

    assert (
        result.failures[0].attempt
        == 1
    )

    assert (
        result.failures[0].error_type
    )

    assert len(
        generator.prompts
    ) == 2


def test_retry_prompt_preserves_original_data_and_adds_feedback(
    monkeypatch,
):
    synthesis_input = _synthesis_input()

    generator = FakeGenerator(
        raw_texts=_valid_response()
    )

    validation_calls = 0

    def reject_first_attempt(
        received_input,
        received_draft,
    ):
        nonlocal validation_calls

        validation_calls += 1

        if validation_calls == 1:
            raise ValueError(
                "semantic validation failed"
            )

    monkeypatch.setattr(
        "equitylens.synthesis_pipeline."
        "validate_synthesis_semantics",
        reject_first_attempt,
    )

    result = run_synthesis(
        synthesis_input,
        generator,
    )

    assert result.attempts == 2

    assert len(
        result.failures
    ) == 1

    failure = result.failures[0]

    assert failure.attempt == 1

    assert (
        failure.error_type
        == "ValueError"
    )

    assert (
        failure.error_message
        == "semantic validation failed"
    )

    assert len(
        generator.prompts
    ) == 2

    original_prompt = (
        generator.prompts[0]
    )

    retry_prompt = (
        generator.prompts[1]
    )

    assert (
        retry_prompt.system_message
        == original_prompt.system_message
    )

    assert (
        synthesis_input.current_document_id
        in retry_prompt.user_message
    )

    assert (
        "RESEARCH_DATA_START"
        in retry_prompt.user_message
    )

    assert (
        "RESEARCH_DATA_END"
        in retry_prompt.user_message
    )

    assert (
        "PREVIOUS_OUTPUT_REJECTED"
        in retry_prompt.user_message
    )

    assert (
        "ValueError"
        in retry_prompt.user_message
    )

    assert (
        "semantic validation failed"
        in retry_prompt.user_message
    )

    assert (
        "Return JSON only."
        in retry_prompt.user_message
    )


def test_run_synthesis_calls_semantic_validator(
    monkeypatch,
):
    synthesis_input = _synthesis_input()

    generator = FakeGenerator(
        raw_texts=_valid_response()
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
        raw_texts=_valid_response()
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

    assert len(
        generator.prompts
    ) == 2


def test_max_attempts_one_disables_retry():
    generator = FakeGenerator(
        raw_texts="not valid json"
    )

    with pytest.raises(
        ValueError,
    ):
        run_synthesis(
            _synthesis_input(),
            generator,
            max_attempts=1,
        )

    assert len(
        generator.prompts
    ) == 1


def test_custom_max_attempts_is_respected():
    generator = FakeGenerator(
        raw_texts=(
            "not valid json",
            "still not valid json",
            _valid_response(),
        )
    )

    result = run_synthesis(
        _synthesis_input(),
        generator,
        max_attempts=3,
    )

    assert result.attempts == 3

    assert len(
        result.failures
    ) == 2

    assert len(
        generator.prompts
    ) == 3


def test_max_attempts_below_one_is_rejected():
    generator = FakeGenerator(
        raw_texts=_valid_response()
    )

    with pytest.raises(
        ValueError,
        match="max_attempts must be at least 1",
    ):
        run_synthesis(
            _synthesis_input(),
            generator,
            max_attempts=0,
        )

    assert generator.prompts == []