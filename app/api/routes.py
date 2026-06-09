from __future__ import annotations

from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    ChunkResponse,
    CrawlReportResponse,
    CrawlRequest,
    CrawlResponse,
    CrawlOutcomeResponse,
    CitationResponse,
    DocSourceResponse,
    EvaluationRequest,
    EvaluationSummaryResponse,
    IndexStatsResponse,
    LLMHealthResponse,
    LLMOptionResponse,
    QueryLogResponse,
    QueryRequest,
    QueryResponse,
    RebuildRequest,
    RebuildResponse,
    SuggestionResponse,
    TopicResponse,
)
from app.config import settings
from app.core.doc_crawler import OfficialDocsCrawler, load_crawl_manifest, load_doc_sources
from app.services.rag_service import RAGService


router = APIRouter()


@lru_cache(maxsize=1)
def get_service() -> RAGService:
    return RAGService.from_directory(
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


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/v1/index/stats", response_model=IndexStatsResponse)
def index_stats() -> IndexStatsResponse:
    service = get_service()
    stats = service.stats()
    return IndexStatsResponse(**stats)


@router.post("/api/v1/index/rebuild", response_model=RebuildResponse)
def rebuild_index(payload: Optional[RebuildRequest] = None) -> RebuildResponse:
    service = get_service()
    rebuilt_topics = payload.topics if payload else []
    stats = service.rebuild(rebuilt_topics or None)
    return RebuildResponse(
        message="Index rebuilt successfully.",
        document_count=stats["document_count"],
        chunk_count=stats["chunk_count"],
        topic_count=stats["topic_count"],
        rebuilt_topics=rebuilt_topics,
        last_rebuild_at=stats["last_rebuild_at"],
    )


@router.post("/api/v1/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    result = get_service().query(
        payload.question,
        top_k=payload.top_k,
        topic=payload.topic,
        llm_provider=payload.llm_provider,
        llm_model=payload.llm_model,
    )
    return QueryResponse(
        question=payload.question,
        answer=result.answer,
        summary=result.summary,
        key_points=result.key_points,
        caveats=result.caveats,
        used_chunk_ids=result.used_chunk_ids,
        topic=result.topic,
        confidence_label=result.confidence_label,
        documentation_hint=result.documentation_hint,
        related_questions=result.related_questions,
        answer_backend=result.answer_backend,
        citations=[
            CitationResponse(
                chunk_id=hit.chunk.chunk_id,
                source=hit.chunk.source,
                source_name=hit.chunk.metadata.get("source_name", hit.chunk.title),
                source_url=hit.chunk.metadata.get("source_url"),
                score=round(hit.score, 4),
                title=hit.chunk.title,
                topic=hit.chunk.metadata.get("topic", "general"),
            )
            for hit in result.hits
        ],
        retrieved_chunks=[
            ChunkResponse(
                chunk_id=hit.chunk.chunk_id,
                source=hit.chunk.source,
                source_name=hit.chunk.metadata.get("source_name", hit.chunk.title),
                source_url=hit.chunk.metadata.get("source_url"),
                title=hit.chunk.title,
                topic=hit.chunk.metadata.get("topic", "general"),
                score=round(hit.score, 4),
                lexical_score=round(hit.lexical_score, 4),
                semantic_score=round(hit.semantic_score, 4),
                rerank_score=(
                    round(hit.rerank_score, 4) if hit.rerank_score is not None else None
                ),
                text=hit.chunk.text,
            )
            for hit in result.hits
        ],
    )


@router.get("/api/v1/topics", response_model=list[TopicResponse])
def topics() -> list[TopicResponse]:
    return [TopicResponse(**item) for item in get_service().topic_catalog()]


@router.get("/api/v1/suggestions", response_model=SuggestionResponse)
def suggestions(topic: Optional[str] = None) -> SuggestionResponse:
    return SuggestionResponse(
        topic=topic,
        questions=get_service().suggested_questions(topic),
    )


@router.get("/api/v1/llm/options", response_model=list[LLMOptionResponse])
def llm_options() -> list[LLMOptionResponse]:
    return [LLMOptionResponse(**item) for item in get_service().llm_catalog()]


@router.get("/api/v1/llm/health", response_model=list[LLMHealthResponse])
def llm_health() -> list[LLMHealthResponse]:
    return [LLMHealthResponse(**item) for item in get_service().llm_health_report()]


@router.get("/api/v1/docs/sources", response_model=list[DocSourceResponse])
def doc_sources() -> list[DocSourceResponse]:
    manifest = load_crawl_manifest(settings.knowledge_base_dir)
    source_entries = load_doc_sources(settings.doc_sources_path)
    response: list[DocSourceResponse] = []
    for source in source_entries:
        topic_dir = settings.knowledge_base_dir / source.topic
        indexed_count = 0
        if topic_dir.exists():
            indexed_count = sum(
                1
                for path in topic_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".md", ".txt"}
            )
        manifest_entries = [
            item for item in manifest.values() if item.get("source_id") == source.source_id
        ]
        last_crawled_at = ""
        if manifest_entries:
            last_crawled_at = max(item.get("updated_at", "") for item in manifest_entries)
        response.append(
            DocSourceResponse(
                source_id=source.source_id,
                topic=source.topic,
                label=source.label,
                description=source.description,
                max_pages=source.max_pages,
                allow_domains=source.allow_domains,
                indexed_document_count=indexed_count,
                crawled_document_count=len(manifest_entries),
                last_crawled_at=last_crawled_at or None,
            )
        )
    return response


@router.post("/api/v1/docs/crawl", response_model=CrawlResponse)
def crawl_docs(payload: CrawlRequest) -> CrawlResponse:
    all_sources = load_doc_sources(settings.doc_sources_path)
    selected_sources = (
        all_sources
        if payload.source_id == "all"
        else [source for source in all_sources if source.source_id == payload.source_id]
    )
    if not selected_sources:
        raise HTTPException(status_code=404, detail=f"Unknown source_id: {payload.source_id}")
    reports = []
    with OfficialDocsCrawler() as crawler:
        for source in selected_sources:
            reports.append(
                crawler.crawl_source_report(
                    source,
                    settings.knowledge_base_dir,
                    page_limit=payload.limit,
                    incremental=payload.incremental,
                )
            )

    affected_topics = sorted(
        {
            report.topic
            for report in reports
            if report.created_count > 0 or report.updated_count > 0
        }
    )
    rebuilt_topics = affected_topics if payload.rebuild_after else []
    index_stats = get_service().rebuild(rebuilt_topics or None) if rebuilt_topics else get_service().stats()
    return CrawlResponse(
        affected_topics=affected_topics,
        rebuilt_topics=rebuilt_topics,
        reports=[
            CrawlReportResponse(
                source_id=report.source_id,
                topic=report.topic,
                source_name=report.source_name,
                created_count=report.created_count,
                updated_count=report.updated_count,
                skipped_count=report.skipped_count,
                error_count=report.error_count,
                errors=report.errors,
                outcomes=[
                    CrawlOutcomeResponse(
                        source_id=outcome.source_id,
                        topic=outcome.topic,
                        source_url=outcome.source_url,
                        file_name=outcome.file_name,
                        output_path=outcome.output_path,
                        action=outcome.action,
                        title=outcome.title,
                    )
                    for outcome in report.outcomes
                ],
            )
            for report in reports
        ],
        index_stats=IndexStatsResponse(**index_stats),
    )


@router.get("/api/v1/admin/logs", response_model=list[QueryLogResponse])
def admin_logs(limit: int = 20) -> list[QueryLogResponse]:
    return [QueryLogResponse(**item) for item in get_service().recent_queries(limit)]


@router.post("/api/v1/evaluation/run", response_model=EvaluationSummaryResponse)
def run_evaluation(payload: EvaluationRequest) -> EvaluationSummaryResponse:
    report = get_service().evaluate(
        settings.eval_cases_path,
        top_k=payload.top_k,
        topic=payload.topic,
        llm_provider=payload.llm_provider,
        llm_model=payload.llm_model,
        limit=payload.limit,
    )
    return EvaluationSummaryResponse(**report)
