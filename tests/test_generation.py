from __future__ import annotations

import unittest

from app.core.generation import GroundedAnswerGenerator
from app.core.types import Chunk, SearchHit


class FakeLLMGenerator:
    def __init__(self, answer: str | None) -> None:
        self.answer = answer

    def generate(self, question: str, topic: str, documentation_hint: str, hits: list[SearchHit]):
        if self.answer is None:
            return None, "extractive-fallback"
        return self.answer, "openai:test-model"


class GroundedAnswerGeneratorTest(unittest.TestCase):
    def test_falls_back_when_llm_unavailable(self) -> None:
        hit = SearchHit(
            chunk=Chunk(
                doc_id="fastapi",
                chunk_id="fastapi-0001",
                source="memory",
                title="FastAPI",
                text="FastAPI dependencies let you reuse shared logic across routes.",
                metadata={"topic": "fastapi"},
            ),
            score=0.8,
            lexical_score=0.4,
            semantic_score=0.9,
        )
        generator = GroundedAnswerGenerator(llm_generator=FakeLLMGenerator(None))

        result = generator.generate("依赖注入能解决什么问题？", [hit], "fastapi")

        self.assertEqual(result.answer_backend, "extractive-fallback")
        self.assertIn("FastAPI dependencies", result.answer)

    def test_prefers_llm_answer_when_available(self) -> None:
        hit = SearchHit(
            chunk=Chunk(
                doc_id="redis",
                chunk_id="redis-0001",
                source="memory",
                title="Redis",
                text="RDB is compact while AOF improves durability.",
                metadata={"topic": "redis"},
            ),
            score=0.8,
            lexical_score=0.4,
            semantic_score=0.9,
        )
        generator = GroundedAnswerGenerator(
            llm_generator=FakeLLMGenerator("这是一个基于证据的回答。[redis-0001]")
        )

        result = generator.generate("RDB 和 AOF 怎么取舍？", [hit], "redis")

        self.assertEqual(result.answer_backend, "openai:test-model")
        self.assertEqual(result.answer, "这是一个基于证据的回答。[redis-0001]")


if __name__ == "__main__":
    unittest.main()
