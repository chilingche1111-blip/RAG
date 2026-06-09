from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter

from app.api.schemas import (
    ChunkResponse,
    CitationResponse,
    IndexStatsResponse,
    QueryRequest,
    QueryResponse,
    RebuildResponse,
    SuggestionResponse,
    TopicResponse,
)
from app.config import settings
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
def rebuild_index() -> RebuildResponse:
    service = get_service()
    stats = service.rebuild()
    return RebuildResponse(
        message="Index rebuilt successfully.",
        document_count=stats["document_count"],
        chunk_count=stats["chunk_count"],
    )


@router.post("/api/v1/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    result = get_service().query(
        payload.question,
        top_k=payload.top_k,
        topic=payload.topic,
    )
    return QueryResponse(
        question=payload.question,
        answer=result.answer,
        topic=result.topic,
        confidence_label=result.confidence_label,
        documentation_hint=result.documentation_hint,
        related_questions=result.related_questions,
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
def suggestions(topic: str | None = None) -> SuggestionResponse:
    return SuggestionResponse(
        topic=topic,
        questions=get_service().suggested_questions(topic),
    )
