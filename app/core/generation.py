from __future__ import annotations

from collections import Counter

from app.core.answer_format import StructuredAnswer
from app.core.llm_generation import MultiProviderLLMGenerator
from app.core.topic_catalog import get_topic_profile
from app.core.text import best_matching_sentences, extract_lexical_terms
from app.core.types import QueryResult, SearchHit


class GroundedAnswerGenerator:
    def __init__(
        self,
        llm_generator: MultiProviderLLMGenerator | None = None,
    ) -> None:
        self.llm_generator = llm_generator

    def generate(
        self,
        question: str,
        hits: list[SearchHit],
        requested_topic: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> QueryResult:
        if not hits:
            empty_answer = StructuredAnswer(
                summary=(
                    "当前索引里的技术文档没有足够证据支撑这个问题。建议你缩小范围，"
                    "或者显式选择一个技术主题，例如 FastAPI、asyncio、Redis、PostgreSQL 或 Docker。"
                ),
                key_points=[],
                caveats=[],
                used_chunk_ids=[],
            )
            return QueryResult(
                answer=empty_answer.to_text(),
                summary=empty_answer.summary,
                key_points=empty_answer.key_points,
                caveats=empty_answer.caveats,
                used_chunk_ids=empty_answer.used_chunk_ids,
                hits=[],
                topic=requested_topic or "general",
                confidence_label="low",
                documentation_hint="优先使用明确的组件名、功能名或 API 名称来提问，检索效果会更稳定。",
                related_questions=[],
                answer_backend="extractive",
            )

        query_terms = extract_lexical_terms(question)
        evidence_lines: list[str] = []
        seen_sources: set[str] = set()

        for hit in hits:
            if hit.chunk.source in seen_sources and len(evidence_lines) >= 2:
                continue
            sentences = best_matching_sentences(hit.chunk.text, query_terms.keys(), 2)
            if sentences:
                evidence_lines.append(sentences[0])
                seen_sources.add(hit.chunk.source)
            if len(evidence_lines) == 3:
                break

        if not evidence_lines:
            evidence_lines = [hits[0].chunk.text[:240].strip()]

        topic = requested_topic or self._detect_topic(hits)
        profile = get_topic_profile(topic)
        documentation_hint = (
            profile.documentation_hint
            if profile
            else "优先把问题绑定到具体框架、库或基础设施组件，再解释行为和限制。"
        )
        related_questions = (
            profile.related_questions[:3]
            if profile
            else self._generic_related_questions(question)
        )
        structured_answer = self._build_fallback_answer(hits, evidence_lines)
        answer_backend = "extractive"

        if self.llm_generator is not None:
            llm_answer, llm_backend = self.llm_generator.generate(
                question=question,
                topic=topic,
                documentation_hint=documentation_hint,
                hits=hits,
                provider_id=llm_provider,
                model_name=llm_model,
            )
            if llm_answer:
                structured_answer = llm_answer
            answer_backend = llm_backend

        return QueryResult(
            answer=structured_answer.to_text(),
            summary=structured_answer.summary,
            key_points=structured_answer.key_points,
            caveats=structured_answer.caveats,
            used_chunk_ids=structured_answer.used_chunk_ids,
            hits=hits,
            topic=topic,
            confidence_label=self._confidence_label(hits[0].score),
            documentation_hint=documentation_hint,
            related_questions=related_questions,
            answer_backend=answer_backend,
        )

    def _detect_topic(self, hits: list[SearchHit]) -> str:
        counter: Counter[str] = Counter()
        for hit in hits:
            topic = hit.chunk.metadata.get("topic", "general")
            counter[topic] += hit.score
        return counter.most_common(1)[0][0] if counter else "general"

    def _confidence_label(self, score: float) -> str:
        if score >= 0.45:
            return "high"
        if score >= 0.2:
            return "medium"
        return "low"

    def _generic_related_questions(self, question: str) -> list[str]:
        return [
            f"如果把这个问题收窄到具体 API 或命令，应该怎样重写：{question}",
            "这个能力在官方文档里通常和哪些相邻概念一起出现？",
            "如果这个行为异常，最值得继续查哪一层文档：框架、运行时还是基础设施？",
        ]

    def _build_fallback_answer(
        self, hits: list[SearchHit], evidence_lines: list[str]
    ) -> StructuredAnswer:
        summary_parts: list[str] = []
        key_points: list[str] = []
        used_chunk_ids: list[str] = []

        for index, hit in enumerate(hits[:3]):
            sentences = best_matching_sentences(hit.chunk.text, [], 2)
            chosen_sentence = evidence_lines[index] if index < len(evidence_lines) else (
                sentences[0] if sentences else hit.chunk.text[:220].strip()
            )
            cited_sentence = f"{chosen_sentence} [{hit.chunk.chunk_id}]"
            if index == 0:
                summary_parts.append(cited_sentence)
            key_points.append(cited_sentence)
            used_chunk_ids.append(hit.chunk.chunk_id)

        summary = " ".join(summary_parts).strip() if summary_parts else "未找到足够证据。"
        caveats = []
        if len(hits) > 1:
            caveats.append(
                "如果需要更确定的结论，建议继续查看上面的原始文档链接并对比相邻章节。 "
                + " ".join(f"[{hit.chunk.chunk_id}]" for hit in hits[:2])
            )

        return StructuredAnswer(
            summary=summary,
            key_points=key_points,
            caveats=caveats,
            used_chunk_ids=used_chunk_ids,
        )
