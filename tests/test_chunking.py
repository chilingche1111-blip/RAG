import unittest

from app.core.chunking import MarkdownChunker
from app.core.types import Document


class MarkdownChunkerTest(unittest.TestCase):
    def test_large_document_is_split_into_multiple_chunks(self) -> None:
        text = (
            "# Title\n\n"
            + "Paragraph about retrieval quality. " * 25
            + "\n\n"
            + "Paragraph about chunk boundaries and answer grounding. " * 25
        )
        document = Document(
            doc_id="doc-1",
            title="Title",
            source="memory",
            text=text,
        )

        chunker = MarkdownChunker(chunk_size=220, overlap=40)
        chunks = chunker.chunk_document(document)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(chunk.chunk_id.startswith("doc-1-") for chunk in chunks))
        self.assertTrue(all(len(chunk.text) <= 220 for chunk in chunks))

    def test_heading_only_chunks_are_not_emitted(self) -> None:
        text = (
            "# Root Title\n\n"
            "## First Section\n\n"
            "FastAPI dependencies inject shared logic into endpoints.\n\n"
            "## Second Section\n\n"
            "Async routes should await non-blocking IO operations."
        )
        document = Document(
            doc_id="doc-2",
            title="Doc 2",
            source="memory",
            text=text,
        )

        chunker = MarkdownChunker(chunk_size=400, overlap=40)
        chunks = chunker.chunk_document(document)

        self.assertTrue(chunks)
        self.assertTrue(all("\n\n" in chunk.text for chunk in chunks))
        self.assertFalse(any(chunk.text.strip().startswith("# Root Title") and len(chunk.text.splitlines()) == 1 for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
