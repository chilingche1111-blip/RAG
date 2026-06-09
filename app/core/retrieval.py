from __future__ import annotations

from typing import Iterable

from app.core.text import (
    cosine_similarity,
    counter_norm,
    extract_lexical_terms,
    extract_semantic_terms,
)
from app.core.types import Chunk, IndexedChunk, SearchHit


class HybridRetriever:
    def __init__(
        self,
        lexical_weight: float = 0.45,
        semantic_weight: float = 0.55,
        min_score: float = 0.08,
    ) -> None:
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        self.min_score = min_score
        self._index: list[IndexedChunk] = []

    def build(self, chunks: Iterable[Chunk]) -> None:
        self._index = []
        for chunk in chunks:
            lexical_terms = extract_lexical_terms(chunk.text)
            semantic_terms = extract_semantic_terms(chunk.text)
            self._index.append(
                IndexedChunk(
                    chunk=chunk,
                    lexical_terms=lexical_terms,
                    semantic_terms=semantic_terms,
                    lexical_norm=counter_norm(lexical_terms),
                    semantic_norm=counter_norm(semantic_terms),
                )
            )

    def search(
        self,
        query: str,
        top_k: int = 4,
        metadata_filter: dict[str, str] | None = None,
    ) -> list[SearchHit]:
        query_lexical = extract_lexical_terms(query)
        query_semantic = extract_semantic_terms(query)
        lexical_norm = counter_norm(query_lexical)
        semantic_norm = counter_norm(query_semantic)
        hits: list[SearchHit] = []

        for item in self._index:
            if metadata_filter and not self._matches_filter(
                item.chunk.metadata, metadata_filter
            ):
                continue
            lexical_score = cosine_similarity(
                query_lexical,
                item.lexical_terms,
                lexical_norm,
                item.lexical_norm,
            )
            semantic_score = cosine_similarity(
                query_semantic,
                item.semantic_terms,
                semantic_norm,
                item.semantic_norm,
            )
            score = (
                self.lexical_weight * lexical_score
                + self.semantic_weight * semantic_score
            )
            if score < self.min_score:
                continue
            hits.append(
                SearchHit(
                    chunk=item.chunk,
                    score=score,
                    lexical_score=lexical_score,
                    semantic_score=semantic_score,
                )
            )

        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]

    @property
    def chunk_count(self) -> int:
        return len(self._index)

    def _matches_filter(
        self, metadata: dict[str, str], metadata_filter: dict[str, str]
    ) -> bool:
        for key, expected in metadata_filter.items():
            value = metadata.get(key)
            if not value or value.lower() != expected.lower():
                return False
        return True
