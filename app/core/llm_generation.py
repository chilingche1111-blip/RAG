from __future__ import annotations

from dataclasses import dataclass

from app.core.types import SearchHit


@dataclass
class OpenAIResponseGenerator:
    model_name: str
    reasoning_effort: str = "minimal"
    max_output_tokens: int = 420
    enabled: bool = True
    _client: object | None = None
    _status: str = "not_loaded"

    def generate(
        self,
        question: str,
        topic: str,
        documentation_hint: str,
        hits: list[SearchHit],
    ) -> tuple[str | None, str]:
        client = self._get_client()
        if client is None or not hits:
            return None, self.backend_name()

        evidence_blocks = []
        for hit in hits[:4]:
            evidence_blocks.append(
                "\n".join(
                    [
                        f"Chunk ID: {hit.chunk.chunk_id}",
                        f"Source: {hit.chunk.metadata.get('source_name', hit.chunk.title)}",
                        f"Topic: {hit.chunk.metadata.get('topic', 'general')}",
                        f"Score: {hit.score:.4f}",
                        "Content:",
                        hit.chunk.text,
                    ]
                )
            )

        developer_prompt = (
            "You answer developer documentation questions using only the provided evidence. "
            "Do not invent APIs, behavior, defaults, or recommendations that are not supported "
            "by the evidence. If the evidence is insufficient, say so clearly. "
            "Answer in Chinese unless the user clearly asks in English. "
            "Keep the answer concise but useful. When making a concrete claim, cite one or more "
            "chunk IDs in square brackets, for example [chunk-0001]."
        )
        user_prompt = "\n\n".join(
            [
                f"Question: {question}",
                f"Selected topic: {topic}",
                f"Documentation hint: {documentation_hint}",
                "Evidence:",
                "\n\n".join(evidence_blocks),
            ]
        )

        request_kwargs: dict[str, object] = {
            "model": self.model_name,
            "input": [
                {"role": "developer", "content": developer_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_output_tokens": self.max_output_tokens,
        }
        if self.reasoning_effort:
            request_kwargs["reasoning"] = {"effort": self.reasoning_effort}

        try:
            response = client.responses.create(**request_kwargs)  # type: ignore[call-arg]
            output_text = getattr(response, "output_text", None)
            if isinstance(output_text, str) and output_text.strip():
                self._status = "ready"
                return output_text.strip(), self.backend_name()
        except Exception:
            self._status = "unavailable"
            return None, self.backend_name()

        self._status = "unavailable"
        return None, self.backend_name()

    def backend_name(self) -> str:
        if not self.enabled:
            return "extractive"
        if self._status == "ready":
            return f"openai:{self.model_name}"
        if self._status == "unavailable":
            return "extractive-fallback"
        return f"openai:{self.model_name}"

    def _get_client(self) -> object | None:
        if not self.enabled:
            self._status = "disabled"
            return None
        if self._client is not None:
            return self._client
        try:
            import os
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self._status = "unavailable"
                return None
            self._client = OpenAI(api_key=api_key)
            self._status = "ready"
        except Exception:
            self._client = None
            self._status = "unavailable"
        return self._client
