from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.rag_service import RAGService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local RAG query demo.")
    parser.add_argument("question", help="Question to ask the RAG system.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of chunks to return.")
    parser.add_argument("--topic", help="Optional technical topic filter.")
    args = parser.parse_args()

    service = RAGService.from_directory("data/knowledge_base")
    result = service.query(
        args.question,
        top_k=args.top_k,
        topic=args.topic,
    )

    print("Question:", args.question)
    print("Topic:", result.topic)
    print("Confidence:", result.confidence_label)
    print("Answer backend:", result.answer_backend)
    print("Answer:", result.answer)
    print("Documentation hint:", result.documentation_hint)
    if result.related_questions:
        print("\nRelated questions:")
        for item in result.related_questions:
            print("-", item)
    print("\nCitations:")
    for hit in result.hits:
        print(f"- {hit.chunk.chunk_id} | {hit.chunk.source} | score={hit.score:.4f}")


if __name__ == "__main__":
    main()
