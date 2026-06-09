import tempfile
import unittest
from pathlib import Path

from app.services.rag_service import RAGService


class RAGServiceTest(unittest.TestCase):
    def test_topic_catalog_and_suggestions_exist(self) -> None:
        service = RAGService.from_directory(
            "data/knowledge_base",
            embedding_enabled=False,
            reranker_enabled=False,
            llm_enabled=False,
        )

        catalog = service.topic_catalog()
        suggestions = service.suggested_questions("docker")
        llm_catalog = service.llm_catalog()
        llm_health = service.llm_health_report()

        self.assertGreaterEqual(len(catalog), 5)
        self.assertGreaterEqual(len(suggestions), 1)
        self.assertIn("official_sources", catalog[0])
        self.assertGreaterEqual(len(llm_catalog), 8)
        self.assertEqual(llm_catalog[0]["provider_id"], "openai")
        self.assertTrue(any(item["provider_id"] == "together" for item in llm_catalog))
        self.assertEqual(len(llm_health), len(llm_catalog))
        self.assertIn("configured", llm_health[0])

    def test_query_returns_requested_topic_when_filtered(self) -> None:
        service = RAGService.from_directory(
            "data/knowledge_base",
            embedding_enabled=False,
            reranker_enabled=False,
            llm_enabled=False,
        )

        result = service.query(
            "FastAPI 的依赖注入适合解决什么问题？",
            topic="fastapi",
            top_k=2,
        )

        self.assertEqual(result.topic, "fastapi")
        self.assertGreaterEqual(len(result.hits), 1)
        self.assertGreaterEqual(len(result.related_questions), 1)

    def test_partial_rebuild_replaces_only_selected_topic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            alpha_dir = root / "alpha"
            beta_dir = root / "beta"
            alpha_dir.mkdir()
            beta_dir.mkdir()
            (alpha_dir / "a.md").write_text(
                "# Alpha\n\nalpha keyword original content.",
                encoding="utf-8",
            )
            (beta_dir / "b.md").write_text(
                "# Beta\n\nbeta keyword stable content.",
                encoding="utf-8",
            )

            service = RAGService.from_directory(
                root,
                embedding_enabled=False,
                reranker_enabled=False,
                llm_enabled=False,
            )
            before = service.query("alpha keyword original", topic="alpha", top_k=1)
            self.assertGreaterEqual(len(before.hits), 1)

            (alpha_dir / "a.md").write_text(
                "# Alpha\n\nalpha keyword replaced content after rebuild.",
                encoding="utf-8",
            )
            service.rebuild(["alpha"])
            after = service.query("replaced content", topic="alpha", top_k=1)
            beta = service.query("beta keyword stable", topic="beta", top_k=1)

            self.assertGreaterEqual(len(after.hits), 1)
            self.assertIn("replaced content", after.hits[0].chunk.text)
            self.assertGreaterEqual(len(beta.hits), 1)
            self.assertIn("stable content", beta.hits[0].chunk.text)

    def test_evaluate_and_recent_queries(self) -> None:
        service = RAGService.from_directory(
            "data/knowledge_base",
            embedding_enabled=False,
            reranker_enabled=False,
            llm_enabled=False,
        )
        service.query("Redis 的 RDB 和 AOF 应该怎样取舍？", topic="redis", top_k=2)

        report = service.evaluate(
            "data/evaluation/devdocs_eval_set.json",
            top_k=2,
            limit=3,
        )

        self.assertEqual(report["total_cases"], 3)
        self.assertIn("overall_pass_rate", report)
        self.assertGreaterEqual(len(service.recent_queries(5)), 1)


if __name__ == "__main__":
    unittest.main()
