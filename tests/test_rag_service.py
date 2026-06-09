import unittest

from app.services.rag_service import RAGService


class RAGServiceTest(unittest.TestCase):
    def test_topic_catalog_and_suggestions_exist(self) -> None:
        service = RAGService.from_directory("data/knowledge_base")

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
        service = RAGService.from_directory("data/knowledge_base")

        result = service.query(
            "FastAPI 的依赖注入适合解决什么问题？",
            topic="fastapi",
            top_k=2,
        )

        self.assertEqual(result.topic, "fastapi")
        self.assertGreaterEqual(len(result.hits), 1)
        self.assertGreaterEqual(len(result.related_questions), 1)


if __name__ == "__main__":
    unittest.main()
