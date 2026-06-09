from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.doc_crawler import OfficialDocsCrawler, load_doc_sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch official docs into the knowledge base.")
    parser.add_argument(
        "--source",
        default="all",
        help="Source id from data/doc_sources.json, or 'all'.",
    )
    parser.add_argument(
        "--config",
        default="data/doc_sources.json",
        help="Path to the source registry JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/knowledge_base",
        help="Directory where markdown knowledge files are written.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional page limit override per source.",
    )
    args = parser.parse_args()

    sources = load_doc_sources(args.config)
    selected_sources = (
        sources
        if args.source == "all"
        else [source for source in sources if source.source_id == args.source]
    )
    if not selected_sources:
        raise SystemExit(f"No source matched: {args.source}")

    with OfficialDocsCrawler() as crawler:
        for source in selected_sources:
            documents = crawler.crawl_source(source, args.output_dir, page_limit=args.limit)
            print(
                f"[{source.source_id}] wrote {len(documents)} documents to {args.output_dir}/{source.topic}"
            )
            for document in documents:
                print(f"- {document.file_name} <- {document.source_url}")


if __name__ == "__main__":
    main()
