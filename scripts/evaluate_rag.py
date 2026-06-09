from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.services.rag_service import RAGService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the built-in RAG evaluation set.")
    parser.add_argument(
        "--cases",
        default=str(settings.eval_cases_path),
        help="Path to the evaluation cases JSON file.",
    )
    parser.add_argument("--top-k", type=int, default=4, help="Retriever top-k.")
    parser.add_argument("--topic", help="Only evaluate a single topic.")
    parser.add_argument("--llm-provider", help="Optional provider override.")
    parser.add_argument("--llm-model", help="Optional model override.")
    parser.add_argument("--limit", type=int, help="Optional case count limit.")
    parser.add_argument(
        "--output-json",
        help="Optional path to write the full evaluation report JSON.",
    )
    args = parser.parse_args()

    service = RAGService.from_directory(
        settings.knowledge_base_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        min_score=settings.min_score,
        lexical_weight=settings.lexical_weight,
        semantic_weight=settings.semantic_weight,
        embedding_enabled=settings.embedding_enabled,
        embedding_model_name=settings.embedding_model_name,
        reranker_enabled=settings.reranker_enabled,
        reranker_model_name=settings.reranker_model_name,
        rerank_candidate_pool=settings.rerank_candidate_pool,
        rerank_weight=settings.rerank_weight,
        llm_enabled=settings.llm_enabled,
        llm_provider=settings.llm_provider,
        llm_model_name=settings.llm_model_name,
        llm_reasoning_effort=settings.llm_reasoning_effort,
        llm_max_output_tokens=settings.llm_max_output_tokens,
        llm_timeout_seconds=settings.llm_timeout_seconds,
        llm_max_retries=settings.llm_max_retries,
        llm_retry_backoff_seconds=settings.llm_retry_backoff_seconds,
        query_log_limit=settings.query_log_size,
    )
    report = service.evaluate(
        args.cases,
        top_k=args.top_k,
        topic=args.topic,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        limit=args.limit,
    )

    print(f"Total cases: {report['total_cases']}")
    print(f"Passed cases: {report['passed_cases']}")
    print(f"Retrieval hit rate: {report['retrieval_hit_rate']:.2%}")
    print(f"Citation hit rate: {report['citation_hit_rate']:.2%}")
    print(f"Answer term coverage: {report['answer_term_coverage']:.2%}")
    print(f"Overall pass rate: {report['overall_pass_rate']:.2%}")
    print("Backends:")
    for backend, count in sorted(report["backend_counts"].items()):
        print(f"- {backend}: {count}")

    failing = [item for item in report["results"] if not item["passed"]]
    if failing:
        print("\nFailing cases:")
        for item in failing[:10]:
            print(
                f"- {item['case_id']} | topic={item['topic']} | "
                f"retrieval_hit={item['retrieval_hit']} | citation_hit={item['citation_hit']} | "
                f"term_coverage={item['answer_term_coverage']}"
            )

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nSaved JSON report to {output_path}")


if __name__ == "__main__":
    main()
