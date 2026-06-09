from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    chunk_id: str
    source: str
    source_name: str
    source_url: Optional[str] = None
    title: str
    topic: str
    score: float


class ChunkResponse(BaseModel):
    chunk_id: str
    source: str
    source_name: str
    source_url: Optional[str] = None
    title: str
    topic: str
    score: float
    lexical_score: float
    semantic_score: float
    rerank_score: Optional[float] = None
    text: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(default=4, ge=1, le=10)
    topic: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    summary: str
    key_points: List[str]
    caveats: List[str]
    used_chunk_ids: List[str]
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
    topic: Optional[str] = None
    questions: List[str]


class LLMOptionResponse(BaseModel):
    provider_id: str
    label: str
    provider_type: str
    api_key_env: str
    default_model: str
    base_url: str
    description: str


class LLMHealthResponse(BaseModel):
    provider_id: str
    label: str
    provider_type: str
    api_key_env: str
    default_model: str
    base_url: str
    description: str
    configured: bool
    status: str
    message: str
    attempts: int
    selected_by_default: bool


class IndexStatsResponse(BaseModel):
    document_count: int
    chunk_count: int
    topic_count: int
    knowledge_base_dir: str
    retrieval_backend: str
    reranker_backend: str
    generation_backend: str
    last_rebuild_at: str
    query_log_size: int


class RebuildRequest(BaseModel):
    topics: List[str] = Field(default_factory=list)


class RebuildResponse(BaseModel):
    message: str
    document_count: int
    chunk_count: int
    topic_count: int
    rebuilt_topics: List[str]
    last_rebuild_at: str


class DocSourceResponse(BaseModel):
    source_id: str
    topic: str
    label: str
    description: str
    max_pages: int
    allow_domains: List[str]
    indexed_document_count: int
    crawled_document_count: int
    last_crawled_at: Optional[str] = None


class CrawlRequest(BaseModel):
    source_id: str = "all"
    limit: Optional[int] = None
    incremental: bool = True
    rebuild_after: bool = True


class CrawlOutcomeResponse(BaseModel):
    source_id: str
    topic: str
    source_url: str
    file_name: str
    output_path: str
    action: str
    title: str


class CrawlReportResponse(BaseModel):
    source_id: str
    topic: str
    source_name: str
    created_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    errors: List[str]
    outcomes: List[CrawlOutcomeResponse]


class CrawlResponse(BaseModel):
    affected_topics: List[str]
    rebuilt_topics: List[str]
    reports: List[CrawlReportResponse]
    index_stats: IndexStatsResponse


class QueryLogResponse(BaseModel):
    timestamp: str
    question: str
    topic: str
    confidence_label: str
    answer_backend: str
    top_chunk_ids: str


class EvaluationRequest(BaseModel):
    top_k: int = Field(default=4, ge=1, le=10)
    topic: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    limit: Optional[int] = Field(default=None, ge=1)


class EvaluationCaseResultResponse(BaseModel):
    case_id: str
    topic: str
    question: str
    answer_backend: str
    confidence_label: str
    expected_chunk_ids: List[str]
    retrieved_chunk_ids: List[str]
    cited_chunk_ids: List[str]
    retrieval_hit: bool
    citation_hit: bool
    answer_term_coverage: float
    passed: bool
    matched_terms: List[str]


class EvaluationSummaryResponse(BaseModel):
    total_cases: int
    passed_cases: int
    retrieval_hit_rate: float
    citation_hit_rate: float
    answer_term_coverage: float
    overall_pass_rate: float
    backend_counts: dict[str, int]
    results: List[EvaluationCaseResultResponse]
