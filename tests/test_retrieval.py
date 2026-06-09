import unittest

from app.core.chunking import MarkdownChunker
from app.core.retrieval import HybridRetriever
from app.core.types import Document


class HybridRetrieverTest(unittest.TestCase):
    def test_query_prefers_retrieval_document(self) -> None:
        documents = [
            Document(
                doc_id="retrieval",
                title="Retrieval",
                source="retrieval.md",
                text=(
                    "# Retrieval\n\n"
                    "Hybrid retrieval combines lexical search and semantic similarity."
                ),
                metadata={"topic": "python"},
            ),
            Document(
                doc_id="evaluation",
                title="Evaluation",
                source="evaluation.md",
                text="# Evaluation\n\nRecall at K is a retrieval metric.",
                metadata={"topic": "database"},
            ),
        ]

        chunks = MarkdownChunker(chunk_size=220, overlap=40).chunk_documents(documents)
        retriever = HybridRetriever(min_score=0.01)
        retriever.build(chunks)

        hits = retriever.search("How does hybrid retrieval improve search?", top_k=2)

        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[0].chunk.doc_id, "retrieval")

    def test_search_supports_metadata_filter(self) -> None:
        documents = [
            Document(
                doc_id="python",
                title="Python",
                source="python.md",
                text="Python list comprehension can improve readability.",
                metadata={"topic": "python"},
            ),
            Document(
                doc_id="network",
                title="Network",
                source="network.md",
                text="TCP handshake confirms both sides can communicate.",
                metadata={"topic": "network"},
            ),
        ]

        chunks = MarkdownChunker(chunk_size=220, overlap=40).chunk_documents(documents)
        retriever = HybridRetriever(min_score=0.01)
        retriever.build(chunks)

        hits = retriever.search(
            "How does handshake work?",
            top_k=2,
            metadata_filter={"topic": "network"},
        )

        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].chunk.doc_id, "network")


if __name__ == "__main__":
    unittest.main()
