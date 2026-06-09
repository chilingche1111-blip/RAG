from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    chunk_id: str
    source: str
    source_name: str
    source_url: str | None = None
    title: str
    topic: str
    score: float


class ChunkResponse(BaseModel):
    chunk_id: str
    source: str
    source_name: str
    source_url: str | None = None
    title: str
    topic: str
    score: float
    lexical_score: float
    semantic_score: float
    rerank_score: float | None = None
    text: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(default=4, ge=1, le=10)
    topic: str | None = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    topic: str
    confidence_label: str
    documentation_hint: str
    related_questions: List[str]
    answer_backend: str
    citations: List[CitationResponse]
    retrieved_chunks: List[ChunkResponse]


class TopicResponse(BaseModel):
    id: str
    label: str
    description: str
    documentation_hint: str
    official_sources: List[dict[str, str]]
    sample_questions: List[str]


class SuggestionResponse(BaseModel):
    topic: str | None = None
    questions: List[str]


class IndexStatsResponse(BaseModel):
    document_count: int
    chunk_count: int
    knowledge_base_dir: str
    retrieval_backend: str
    reranker_backend: str
    generation_backend: str


class RebuildResponse(BaseModel):
    message: str
    document_count: int
    chunk_count: int
