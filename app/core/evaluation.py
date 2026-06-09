from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional

if TYPE_CHECKING:
    from app.services.rag_service import RAGService


MIN_ANSWER_TERM_COVERAGE = 0.33


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    question: str
    topic: Optional[str] = None
    expected_chunk_ids: list[str] = field(default_factory=list)
    required_terms: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    topic: str
    question: str
    answer_backend: str
    confidence_label: str
    expected_chunk_ids: list[str]
    retrieved_chunk_ids: list[str]
    cited_chunk_ids: list[str]
    retrieval_hit: bool
    citation_hit: bool
    answer_term_coverage: float
    passed: bool
    matched_terms: list[str]


@dataclass(frozen=True)
class EvalSummary:
    total_cases: int
    passed_cases: int
    retrieval_hit_rate: float
    citation_hit_rate: float
    answer_term_coverage: float
    overall_pass_rate: float
    backend_counts: dict[str, int]
    results: list[EvalCaseResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "retrieval_hit_rate": self.retrieval_hit_rate,
            "citation_hit_rate": self.citation_hit_rate,
            "answer_term_coverage": self.answer_term_coverage,
            "overall_pass_rate": self.overall_pass_rate,
            "backend_counts": self.backend_counts,
            "results": [asdict(item) for item in self.results],
        }


def load_eval_cases(path: str | Path) -> list[EvalCase]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases: list[EvalCase] = []
    for item in payload:
        cases.append(
            EvalCase(
                case_id=str(item["case_id"]),
                question=str(item["question"]),
                topic=str(item.get("topic")).strip() or None if item.get("topic") is not None else None,
                expected_chunk_ids=[
                    str(chunk_id).strip()
                    for chunk_id in item.get("expected_chunk_ids", [])
                    if str(chunk_id).strip()
                ],
                required_terms=[
                    str(term).strip().lower()
                    for term in item.get("required_terms", [])
                    if str(term).strip()
                ],
                notes=str(item.get("notes", "")).strip(),
            )
        )
    return cases


def evaluate_cases(
    service: "RAGService",
    cases: Iterable[EvalCase],
    top_k: int = 4,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> EvalSummary:
    results: list[EvalCaseResult] = []
    backend_counts: dict[str, int] = {}

    for case in cases:
        query_result = service.query(
            case.question,
            top_k=top_k,
            topic=case.topic,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
        retrieved_chunk_ids = [hit.chunk.chunk_id for hit in query_result.hits]
        cited_chunk_ids = list(query_result.used_chunk_ids)
        retrieval_hit = _contains_any(case.expected_chunk_ids, retrieved_chunk_ids)
        citation_hit = _contains_any(case.expected_chunk_ids, cited_chunk_ids)
        answer_text = " ".join(
            [query_result.summary] + query_result.key_points + query_result.caveats
        ).lower()
        matched_terms = [
            term for term in case.required_terms if term and term.lower() in answer_text
        ]
        answer_term_coverage = _ratio(len(matched_terms), len(case.required_terms))
        passed = (
            retrieval_hit
            and citation_hit
            and answer_term_coverage >= MIN_ANSWER_TERM_COVERAGE
        )
        backend_counts[query_result.answer_backend] = (
            backend_counts.get(query_result.answer_backend, 0) + 1
        )
        results.append(
            EvalCaseResult(
                case_id=case.case_id,
                topic=case.topic or query_result.topic,
                question=case.question,
                answer_backend=query_result.answer_backend,
                confidence_label=query_result.confidence_label,
                expected_chunk_ids=case.expected_chunk_ids,
                retrieved_chunk_ids=retrieved_chunk_ids,
                cited_chunk_ids=cited_chunk_ids,
                retrieval_hit=retrieval_hit,
                citation_hit=citation_hit,
                answer_term_coverage=round(answer_term_coverage, 4),
                passed=passed,
                matched_terms=matched_terms,
            )
        )

    total_cases = len(results)
    passed_cases = sum(1 for item in results if item.passed)
    retrieval_hits = sum(1 for item in results if item.retrieval_hit)
    citation_hits = sum(1 for item in results if item.citation_hit)
    total_term_coverage = sum(item.answer_term_coverage for item in results)

    return EvalSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        retrieval_hit_rate=round(_ratio(retrieval_hits, total_cases), 4),
        citation_hit_rate=round(_ratio(citation_hits, total_cases), 4),
        answer_term_coverage=round(_ratio(total_term_coverage, total_cases), 4),
        overall_pass_rate=round(_ratio(passed_cases, total_cases), 4),
        backend_counts=backend_counts,
        results=results,
    )


def _contains_any(expected_chunk_ids: list[str], actual_chunk_ids: list[str]) -> bool:
    if not expected_chunk_ids:
        return True
    actual = {item.strip() for item in actual_chunk_ids if item.strip()}
    return any(item in actual for item in expected_chunk_ids)


def _ratio(numerator: float, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator
