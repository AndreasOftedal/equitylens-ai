from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from equitylens.synthesis_prompt import SynthesisPrompt

DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT = "low"


SYNTHESIS_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "schema_version": {
            "type": "string",
        },
        "title": {
            "type": "string",
        },
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "claim_id": {
                        "type": "string",
                    },
                    "claim_type": {
                        "type": "string",
                        "enum": [
                            "financial_observation",
                            "management_explanation",
                            "consistency_observation",
                            "guidance_update",
                        ],
                    },
                    "text": {
                        "type": "string",
                    },
                    "metric_id": {
                        "type": "string",
                    },
                    "target_period": {
                        "anyOf": [
                            {
                                "type": "string",
                            },
                            {
                                "type": "null",
                            },
                        ],
                    },
                    "source_fact_ids": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                    "evidence_sentence_ids": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                },
                "required": [
                    "claim_id",
                    "claim_type",
                    "text",
                    "metric_id",
                    "target_period",
                    "source_fact_ids",
                    "evidence_sentence_ids",
                ],
            },
        },
        "limitations": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "schema_version",
        "title",
        "claims",
        "limitations",
    ],
}


@dataclass(frozen=True)
class SynthesisLLMResponse:
    raw_text: str
    model: str


class OpenAISynthesisClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        client: Any | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError(
                "model cannot be empty."
            )

        self._model = model.strip()

        self._client = (
            client
            if client is not None
            else OpenAI()
        )

    @property
    def model(
        self,
    ) -> str:
        return self._model

    def generate(
        self,
        prompt: SynthesisPrompt,
    ) -> SynthesisLLMResponse:
        if not prompt.system_message.strip():
            raise ValueError(
                "system_message cannot be empty."
            )

        if not prompt.user_message.strip():
            raise ValueError(
                "user_message cannot be empty."
            )

        response = (
            self._client.responses.create(
                model=self._model,
                reasoning={
                    "effort": (
                        DEFAULT_REASONING_EFFORT
                    ),
                },
                instructions=(
                    prompt.system_message
                ),
                input=prompt.user_message,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": (
                            "equitylens_synthesis"
                        ),
                        "strict": True,
                        "schema": (
                            SYNTHESIS_JSON_SCHEMA
                        ),
                    },
                },
            )
        )

        raw_text = response.output_text

        if not isinstance(
            raw_text,
            str,
        ):
            raise TypeError(
                "OpenAI response did not contain "
                "string output_text."
            )

        raw_text = raw_text.strip()

        if not raw_text:
            raise RuntimeError(
                "OpenAI response contained empty "
                "output_text."
            )

        return SynthesisLLMResponse(
            raw_text=raw_text,
            model=self._model,
        )