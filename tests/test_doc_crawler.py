from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.doc_crawler import (
    CrawledDocument,
    extract_markdown_from_html,
    load_crawl_manifest,
    load_doc_sources,
    normalize_url,
    render_crawled_document,
    save_crawl_manifest,
    slugify_url,
)


class DocCrawlerTest(unittest.TestCase):
    def test_extract_markdown_from_html(self) -> None:
        html = """
        <html>
          <head><title>Sample Doc</title></head>
          <body>
            <main>
              <h1>Sample Doc</h1>
              <p>Paragraph one.</p>
              <h2>Section</h2>
              <p>Paragraph two.</p>
              <pre><code>pip install demo</code></pre>
            </main>
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")

        title, markdown = extract_markdown_from_html(soup, "https://example.com/docs/sample")

        self.assertEqual(title, "Sample Doc")
        self.assertIn("# Sample Doc", markdown)
        self.assertIn("Paragraph one.", markdown)
        self.assertIn("```text", markdown)

    def test_slugify_url(self) -> None:
        slug = slugify_url("https://docs.example.com/path/to/page/")
        self.assertEqual(slug, "docs-example-com-path-to-page")

    def test_load_doc_sources(self) -> None:
        payload = [
            {
                "source_id": "sample",
                "topic": "sample-topic",
                "label": "Sample",
                "start_urls": ["https://example.com/docs"],
                "allow_domains": ["example.com"],
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sources.json"
            config_path.write_text(json.dumps(payload), encoding="utf-8")
            sources = load_doc_sources(config_path)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].source_id, "sample")

    def test_normalize_url_removes_fragment_and_trailing_slash(self) -> None:
        normalized = normalize_url("https://example.com/docs/page/#section")
        self.assertEqual(normalized, "https://example.com/docs/page")

    def test_render_document_and_manifest_roundtrip(self) -> None:
        document = CrawledDocument(
            source_id="sample",
            topic="sample-topic",
            source_name="Sample Docs",
            source_url="https://example.com/docs/sample",
            title="Sample Doc",
            markdown="# Sample Doc\n\nBody",
            file_name="sample.md",
        )
        rendered = render_crawled_document(document)
        self.assertIn("source_id: sample", rendered)

        manifest = {
            document.source_url: {
                "source_id": document.source_id,
                "topic": document.topic,
                "file_name": document.file_name,
                "output_path": "data/knowledge_base/sample-topic/sample.md",
                "title": document.title,
                "content_sha256": "abc123",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            save_crawl_manifest(temp_dir, manifest)
            loaded = load_crawl_manifest(temp_dir)
        self.assertEqual(loaded[document.source_url]["title"], "Sample Doc")


if __name__ == "__main__":
    unittest.main()
