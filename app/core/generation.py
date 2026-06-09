from __future__ import annotations

from collections import Counter

from app.core.llm_generation import OpenAIResponseGenerator
from app.core.topic_catalog import get_topic_profile
from app.core.text import best_matching_sentences, extract_lexical_terms
from app.core.types import QueryResult, SearchHit


class GroundedAnswerGenerator:
    def __init__(
        self,
        llm_generator: OpenAIResponseGenerator | None = None,
    ) -> None:
        self.llm_generator = llm_generator

    def generate(
        self,
        question: str,
        hits: list[SearchHit],
        requested_topic: str | None = None,
    ) -> QueryResult:
        if not hits:
            return QueryResult(
                answer=(
                    "当前索引里的技术文档没有足够证据支撑这个问题。建议你缩小范围，"
                    "或者显式选择一个技术主题，例如 FastAPI、asyncio、Redis、PostgreSQL 或 Docker。"
                ),
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
        answer = " ".join(evidence_lines)
        answer_backend = "extractive"

        if self.llm_generator is not None:
            llm_answer, llm_backend = self.llm_generator.generate(
                question=question,
                topic=topic,
                documentation_hint=documentation_hint,
                hits=hits,
            )
            if llm_answer:
                answer = llm_answer
            answer_backend = llm_backend

        return QueryResult(
            answer=answer,
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
