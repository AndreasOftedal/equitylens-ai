from dataclasses import dataclass
from typing import Protocol

from equitylens.synthesis_input import SynthesisInput
from equitylens.synthesis_llm import SynthesisLLMResponse
from equitylens.synthesis_output import SynthesisDraft
from equitylens.synthesis_parser import parse_synthesis_response
from equitylens.synthesis_prompt import SynthesisPrompt, build_synthesis_prompt
from equitylens.synthesis_semantics import validate_synthesis_semantics


class SynthesisGenerator(Protocol):
    def generate(
        self,
        prompt: SynthesisPrompt,
    ) -> SynthesisLLMResponse: ...


@dataclass(frozen=True)
class ValidatedSynthesis:
    draft: SynthesisDraft
    model: str


def run_synthesis(
    synthesis_input: SynthesisInput,
    generator: SynthesisGenerator,
) -> ValidatedSynthesis:
    """
    Run the guarded EquityLens synthesis pipeline.

    Raw model output is never returned as an accepted
    synthesis result. It must first pass the strict JSON
    parser and deterministic semantic validation.
    """
    prompt = build_synthesis_prompt(
        synthesis_input
    )

    response = generator.generate(
        prompt
    )

    draft = parse_synthesis_response(
        response.raw_text
    )

    validate_synthesis_semantics(
        synthesis_input,
        draft,
    )

    return ValidatedSynthesis(
        draft=draft,
        model=response.model,
    )