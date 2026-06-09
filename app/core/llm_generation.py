from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from app.core.answer_format import StructuredAnswer
from app.core.types import SearchHit


@dataclass(frozen=True)
class LLMProviderOption:
    provider_id: str
    label: str
    provider_type: str
    api_key_env: str
    default_model: str
    base_url: str | None = None
    description: str = ""


DEFAULT_PROVIDER_OPTIONS: dict[str, LLMProviderOption] = {
    "openai": LLMProviderOption(
        provider_id="openai",
        label="OpenAI",
        provider_type="openai_responses",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-5.4-mini",
        description="OpenAI Responses API with structured JSON schema output.",
    ),
    "anthropic": LLMProviderOption(
        provider_id="anthropic",
        label="Claude",
        provider_type="anthropic_messages",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-sonnet-4-20250514",
        description="Anthropic Messages API for Claude models.",
    ),
    "deepseek": LLMProviderOption(
        provider_id="deepseek",
        label="DeepSeek",
        provider_type="openai_compatible_chat",
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        base_url="https://api.deepseek.com",
        description="DeepSeek OpenAI-compatible API.",
    ),
    "groq": LLMProviderOption(
        provider_id="groq",
        label="Groq",
        provider_type="openai_compatible_chat",
        api_key_env="GROQ_API_KEY",
        default_model="openai/gpt-oss-20b",
        base_url="https://api.groq.com/openai/v1",
        description="Groq OpenAI-compatible API.",
    ),
    "openrouter": LLMProviderOption(
        provider_id="openrouter",
        label="OpenRouter",
        provider_type="openai_compatible_chat",
        api_key_env="OPENROUTER_API_KEY",
        default_model="openai/gpt-4.1-mini",
        base_url="https://openrouter.ai/api/v1",
        description="OpenRouter unified API for many upstream models.",
    ),
    "together": LLMProviderOption(
        provider_id="together",
        label="Together",
        provider_type="openai_compatible_chat",
        api_key_env="TOGETHER_API_KEY",
        default_model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        base_url="https://api.together.xyz/v1",
        description="Together AI OpenAI-compatible API.",
    ),
    "moonshot": LLMProviderOption(
        provider_id="moonshot",
        label="Moonshot Kimi",
        provider_type="openai_compatible_chat",
        api_key_env="MOONSHOT_API_KEY",
        default_model="kimi-k2-0711-preview",
        base_url="https://api.moonshot.cn/v1",
        description="Moonshot Kimi OpenAI-compatible API.",
    ),
    "siliconflow": LLMProviderOption(
        provider_id="siliconflow",
        label="SiliconFlow",
        provider_type="openai_compatible_chat",
        api_key_env="SILICONFLOW_API_KEY",
        default_model="Qwen/Qwen2.5-72B-Instruct",
        base_url="https://api.siliconflow.cn/v1",
        description="SiliconFlow OpenAI-compatible API.",
    ),
    "dashscope": LLMProviderOption(
        provider_id="dashscope",
        label="DashScope Qwen",
        provider_type="openai_compatible_chat",
        api_key_env="DASHSCOPE_API_KEY",
        default_model="qwen-plus",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="Alibaba DashScope compatible-mode API.",
    ),
    "mistral": LLMProviderOption(
        provider_id="mistral",
        label="Mistral",
        provider_type="openai_compatible_chat",
        api_key_env="MISTRAL_API_KEY",
        default_model="mistral-small-latest",
        base_url="https://api.mistral.ai/v1",
        description="Mistral API via OpenAI-compatible chat completions.",
    ),
    "perplexity": LLMProviderOption(
        provider_id="perplexity",
        label="Perplexity",
        provider_type="openai_compatible_chat",
        api_key_env="PERPLEXITY_API_KEY",
        default_model="sonar-pro",
        base_url="https://api.perplexity.ai",
        description="Perplexity API via OpenAI-compatible chat completions.",
    ),
}


def load_provider_options() -> dict[str, LLMProviderOption]:
    providers = dict(DEFAULT_PROVIDER_OPTIONS)
    raw_config = os.getenv("RAG_EXTRA_LLM_PROVIDERS_JSON", "").strip()
    if not raw_config:
        return providers
    try:
        payload = json.loads(raw_config)
    except json.JSONDecodeError:
        return providers
    if not isinstance(payload, list):
        return providers

    for item in payload:
        if not isinstance(item, dict):
            continue
        provider_id = str(item.get("provider_id", "")).strip()
        provider_type = str(item.get("provider_type", "")).strip()
        api_key_env = str(item.get("api_key_env", "")).strip()
        default_model = str(item.get("default_model", "")).strip()
        if not provider_id or not provider_type or not api_key_env or not default_model:
            continue
        providers[provider_id] = LLMProviderOption(
            provider_id=provider_id,
            label=str(item.get("label", provider_id)).strip() or provider_id,
            provider_type=provider_type,
            api_key_env=api_key_env,
            default_model=default_model,
            base_url=str(item.get("base_url", "")).strip() or None,
            description=str(item.get("description", "")).strip(),
        )
    return providers


@dataclass
class MultiProviderLLMGenerator:
    default_provider_id: str
    default_model_name: str
    reasoning_effort: str = "minimal"
    max_output_tokens: int = 420
    enabled: bool = True

    def __post_init__(self) -> None:
        self.provider_options = load_provider_options()
        self._clients: dict[str, object] = {}
        self._status: dict[str, str] = {}

    def generate(
        self,
        question: str,
        topic: str,
        documentation_hint: str,
        hits: list[SearchHit],
        provider_id: str | None = None,
        model_name: str | None = None,
    ) -> tuple[StructuredAnswer | None, str]:
        if not self.enabled or not hits:
            return None, "extractive"

        selected_provider = self._resolve_provider(provider_id)
        if selected_provider is None:
            return None, "extractive-fallback"
        selected_model = model_name or selected_provider.default_model or self.default_model_name
        evidence_blocks = self._build_evidence_blocks(hits)
        structured_instruction = self._structured_instruction()

        if selected_provider.provider_type == "openai_responses":
            return self._generate_openai_responses(
                selected_provider,
                selected_model,
                question,
                topic,
                documentation_hint,
                evidence_blocks,
            )
        if selected_provider.provider_type == "anthropic_messages":
            return self._generate_anthropic_messages(
                selected_provider,
                selected_model,
                question,
                topic,
                documentation_hint,
                evidence_blocks,
            )
        if selected_provider.provider_type == "openai_compatible_chat":
            return self._generate_openai_compatible_chat(
                selected_provider,
                selected_model,
                question,
                topic,
                documentation_hint,
                evidence_blocks,
                structured_instruction,
            )
        return None, "extractive-fallback"

    def backend_name(self, provider_id: str | None = None) -> str:
        if not self.enabled:
            return "extractive"
        provider = self._resolve_provider(provider_id)
        if provider is None:
            return "extractive-fallback"
        status = self._status.get(provider.provider_id)
        if status == "ready":
            return f"{provider.provider_id}:{provider.default_model}"
        if status == "unavailable":
            return "extractive-fallback"
        if not os.getenv(provider.api_key_env):
            return "extractive-fallback"
        return f"{provider.provider_id}:{provider.default_model}"

    def provider_catalog(self) -> list[dict[str, str]]:
        return [
            {
                "provider_id": item.provider_id,
                "label": item.label,
                "provider_type": item.provider_type,
                "api_key_env": item.api_key_env,
                "default_model": item.default_model,
                "base_url": item.base_url or "",
                "description": item.description,
            }
            for item in self.provider_options.values()
        ]

    def provider_health_report(self) -> list[dict[str, str | bool]]:
        report: list[dict[str, str | bool]] = []
        for item in self.provider_options.values():
            configured = bool(os.getenv(item.api_key_env))
            status = "configured" if configured else "missing_key"
            message = (
                f"Environment variable {item.api_key_env} is available."
                if configured
                else f"Environment variable {item.api_key_env} is not set."
            )
            report.append(
                {
                    "provider_id": item.provider_id,
                    "label": item.label,
                    "provider_type": item.provider_type,
                    "api_key_env": item.api_key_env,
                    "default_model": item.default_model,
                    "base_url": item.base_url or "",
                    "description": item.description,
                    "configured": configured,
                    "status": status,
                    "message": message,
                    "selected_by_default": item.provider_id == self.default_provider_id,
                }
            )
        return report

    def _resolve_provider(self, provider_id: str | None) -> LLMProviderOption | None:
        selected = provider_id or self.default_provider_id
        return self.provider_options.get(selected)

    def _build_evidence_blocks(self, hits: list[SearchHit]) -> str:
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
        return "\n\n".join(evidence_blocks)

    def _structured_instruction(self) -> str:
        return (
            "Return valid JSON only with this exact schema: "
            "{\"summary\": string, "
            "\"key_points\": [{\"text\": string, \"citations\": [string]}], "
            "\"caveats\": [{\"text\": string, \"citations\": [string]}], "
            "\"used_chunk_ids\": [string]}. "
            "Use Chinese unless the user clearly asks for English. "
            "Do not invent APIs, behavior, defaults, or recommendations not supported by evidence. "
            "Every concrete claim in summary, key_points, or caveats must include one or more chunk IDs in square brackets or in the citations array."
        )

    def _generate_openai_responses(
        self,
        provider: LLMProviderOption,
        model_name: str,
        question: str,
        topic: str,
        documentation_hint: str,
        evidence_blocks: str,
    ) -> tuple[StructuredAnswer | None, str]:
        client = self._get_openai_client(provider)
        if client is None:
            return None, "extractive-fallback"

        request_kwargs: dict[str, Any] = {
            "model": model_name,
            "input": [
                {
                    "role": "developer",
                    "content": (
                        "You answer developer documentation questions using only the provided evidence. "
                        + self._structured_instruction()
                    ),
                },
                {
                    "role": "user",
                    "content": "\n\n".join(
                        [
                            f"Question: {question}",
                            f"Selected topic: {topic}",
                            f"Documentation hint: {documentation_hint}",
                            "Evidence:",
                            evidence_blocks,
                        ]
                    ),
                },
            ],
            "max_output_tokens": self.max_output_tokens,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "structured_devdocs_answer",
                    "strict": True,
                    "schema": self._json_schema(),
                }
            },
        }
        if self.reasoning_effort:
            request_kwargs["reasoning"] = {"effort": self.reasoning_effort}

        try:
            response = client.responses.create(**request_kwargs)  # type: ignore[call-arg]
            output_text = getattr(response, "output_text", None)
            parsed = self._parse_structured_output(output_text)
            if parsed is not None:
                self._status[provider.provider_id] = "ready"
                return parsed, f"{provider.provider_id}:{model_name}"
        except Exception:
            self._status[provider.provider_id] = "unavailable"
            return None, "extractive-fallback"

        self._status[provider.provider_id] = "unavailable"
        return None, "extractive-fallback"

    def _generate_openai_compatible_chat(
        self,
        provider: LLMProviderOption,
        model_name: str,
        question: str,
        topic: str,
        documentation_hint: str,
        evidence_blocks: str,
        structured_instruction: str,
    ) -> tuple[StructuredAnswer | None, str]:
        client = self._get_openai_client(provider)
        if client is None:
            return None, "extractive-fallback"

        messages = [
            {
                "role": "system",
                "content": (
                    "You answer developer documentation questions using only the provided evidence. "
                    + structured_instruction
                ),
            },
            {
                "role": "user",
                "content": "\n\n".join(
                    [
                        f"Question: {question}",
                        f"Selected topic: {topic}",
                        f"Documentation hint: {documentation_hint}",
                        "Evidence:",
                        evidence_blocks,
                    ]
                ),
            },
        ]
        request_kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            response = client.chat.completions.create(**request_kwargs)  # type: ignore[call-arg]
            content = response.choices[0].message.content  # type: ignore[index]
            parsed = self._parse_structured_output(content)
            if parsed is not None:
                self._status[provider.provider_id] = "ready"
                return parsed, f"{provider.provider_id}:{model_name}"
        except Exception:
            self._status[provider.provider_id] = "unavailable"
            return None, "extractive-fallback"

        self._status[provider.provider_id] = "unavailable"
        return None, "extractive-fallback"

    def _generate_anthropic_messages(
        self,
        provider: LLMProviderOption,
        model_name: str,
        question: str,
        topic: str,
        documentation_hint: str,
        evidence_blocks: str,
    ) -> tuple[StructuredAnswer | None, str]:
        client = self._get_anthropic_client(provider)
        if client is None:
            return None, "extractive-fallback"

        system_prompt = (
            "You answer developer documentation questions using only the provided evidence. "
            + self._structured_instruction()
        )
        user_prompt = "\n\n".join(
            [
                f"Question: {question}",
                f"Selected topic: {topic}",
                f"Documentation hint: {documentation_hint}",
                "Evidence:",
                evidence_blocks,
            ]
        )
        try:
            response = client.messages.create(  # type: ignore[call-arg]
                model=model_name,
                max_tokens=self.max_output_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = self._extract_anthropic_text(response)
            parsed = self._parse_structured_output(raw_text)
            if parsed is not None:
                self._status[provider.provider_id] = "ready"
                return parsed, f"{provider.provider_id}:{model_name}"
        except Exception:
            self._status[provider.provider_id] = "unavailable"
            return None, "extractive-fallback"

        self._status[provider.provider_id] = "unavailable"
        return None, "extractive-fallback"

    def _get_openai_client(self, provider: LLMProviderOption) -> object | None:
        cache_key = provider.provider_id
        if cache_key in self._clients:
            return self._clients[cache_key]
        api_key = os.getenv(provider.api_key_env)
        if not api_key:
            self._status[provider.provider_id] = "unavailable"
            return None
        try:
            from openai import OpenAI

            kwargs: dict[str, Any] = {"api_key": api_key}
            if provider.base_url:
                kwargs["base_url"] = provider.base_url
            client = OpenAI(**kwargs)
            self._clients[cache_key] = client
            return client
        except Exception:
            self._status[provider.provider_id] = "unavailable"
            return None

    def _get_anthropic_client(self, provider: LLMProviderOption) -> object | None:
        cache_key = provider.provider_id
        if cache_key in self._clients:
            return self._clients[cache_key]
        api_key = os.getenv(provider.api_key_env)
        if not api_key:
            self._status[provider.provider_id] = "unavailable"
            return None
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
            self._clients[cache_key] = client
            return client
        except Exception:
            self._status[provider.provider_id] = "unavailable"
            return None

    def _json_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "key_points": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "citations": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["text", "citations"],
                        "additionalProperties": False,
                    },
                },
                "caveats": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "citations": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["text", "citations"],
                        "additionalProperties": False,
                    },
                },
                "used_chunk_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["summary", "key_points", "caveats", "used_chunk_ids"],
            "additionalProperties": False,
        }

    def _extract_anthropic_text(self, response: object) -> str | None:
        content = getattr(response, "content", None)
        if not isinstance(content, list):
            return None
        text_parts: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if isinstance(text, str):
                text_parts.append(text)
        return "\n".join(text_parts).strip() if text_parts else None

    def _parse_structured_output(self, output_text: str | None) -> StructuredAnswer | None:
        if not output_text or not isinstance(output_text, str):
            return None
        json_text = self._extract_json_block(output_text)
        if json_text is None:
            return None
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        summary = str(payload.get("summary", "")).strip()
        raw_key_points = payload.get("key_points", [])
        raw_caveats = payload.get("caveats", [])
        raw_chunk_ids = payload.get("used_chunk_ids", [])
        if not summary:
            return None

        key_points = self._normalize_items(raw_key_points)
        caveats = self._normalize_items(raw_caveats)
        used_chunk_ids = [
            str(chunk_id).strip() for chunk_id in raw_chunk_ids if str(chunk_id).strip()
        ]
        return StructuredAnswer(
            summary=summary,
            key_points=key_points,
            caveats=caveats,
            used_chunk_ids=used_chunk_ids,
        )

    def _normalize_items(self, raw_items: object) -> list[str]:
        if not isinstance(raw_items, list):
            return []
        normalized: list[str] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", "")).strip()
            citations = item.get("citations", [])
            if not text:
                continue
            citation_suffix = ""
            if isinstance(citations, list):
                suffix_parts = [f"[{str(citation).strip()}]" for citation in citations if str(citation).strip()]
                citation_suffix = " ".join(suffix_parts)
            normalized.append(
                f"{text} {citation_suffix}".strip() if citation_suffix and citation_suffix not in text else text
            )
        return normalized

    def _extract_json_block(self, output_text: str) -> str | None:
        fenced_match = re.search(r"```json\s*(\{.*\})\s*```", output_text, re.DOTALL)
        if fenced_match:
            return fenced_match.group(1)
        start = output_text.find("{")
        end = output_text.rfind("}")
        if start == -1 or end == -1 or start >= end:
            return None
        return output_text[start : end + 1]
