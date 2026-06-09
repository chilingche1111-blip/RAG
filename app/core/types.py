from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    source: str
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    chunk_id: str
    source: str
    title: str
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class IndexedChunk:
    chunk: Chunk
    lexical_terms: Counter[str]
    semantic_terms: Counter[str]
    lexical_norm: float
    semantic_norm: float
    dense_embedding: list[float] | None = None


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float
    lexical_score: float
    semantic_score: float
    rerank_score: float | None = None


@dataclass(frozen=True)
class QueryResult:
    answer: str
    hits: List[SearchHit]
    topic: str
    confidence_label: str
    documentation_hint: str
    related_questions: List[str]
    answer_backend: str
