from __future__ import annotations

from typing import Iterable

from app.core.dense_models import CrossEncoderReranker, SentenceTransformerEncoder
from app.core.text import (
    cosine_similarity,
    counter_norm,
    dense_dot_similarity,
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
        embedding_encoder: SentenceTransformerEncoder | None = None,
        reranker: CrossEncoderReranker | None = None,
        rerank_candidate_pool: int = 8,
        rerank_weight: float = 0.65,
    ) -> None:
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        self.min_score = min_score
        self.embedding_encoder = embedding_encoder
        self.reranker = reranker
        self.rerank_candidate_pool = rerank_candidate_pool
        self.rerank_weight = rerank_weight
        self._index: list[IndexedChunk] = []

    def build(self, chunks: Iterable[Chunk]) -> None:
        chunk_list = list(chunks)
        dense_vectors = self._encode_dense_vectors(chunk_list)
        self._index = []
        for index, chunk in enumerate(chunk_list):
            lexical_terms = extract_lexical_terms(chunk.text)
            semantic_terms = extract_semantic_terms(chunk.text)
            self._index.append(
                IndexedChunk(
                    chunk=chunk,
                    lexical_terms=lexical_terms,
                    semantic_terms=semantic_terms,
                    lexical_norm=counter_norm(lexical_terms),
                    semantic_norm=counter_norm(semantic_terms),
                    dense_embedding=dense_vectors[index] if dense_vectors else None,
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
        query_dense = self._encode_query(query)
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
            semantic_score = self._semantic_score(
                query_semantic,
                semantic_norm,
                query_dense,
                item,
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
        return self._rerank(query, hits, top_k)

    @property
    def chunk_count(self) -> int:
        return len(self._index)

    @property
    def retrieval_backend(self) -> str:
        if self.embedding_encoder is None:
            return "lexical+hash"
        return f"lexical+{self.embedding_encoder.backend_name()}"

    @property
    def reranker_backend(self) -> str:
        if self.reranker is None:
            return "disabled"
        return self.reranker.backend_name()

    def _matches_filter(
        self, metadata: dict[str, str], metadata_filter: dict[str, str]
    ) -> bool:
        for key, expected in metadata_filter.items():
            value = metadata.get(key)
            if not value or value.lower() != expected.lower():
                return False
        return True

    def _encode_dense_vectors(
        self, chunks: list[Chunk]
    ) -> list[list[float]] | None:
        if self.embedding_encoder is None or not chunks:
            return None
        return self.embedding_encoder.encode([chunk.text for chunk in chunks])

    def _encode_query(self, query: str) -> list[float] | None:
        if self.embedding_encoder is None:
            return None
        dense_vectors = self.embedding_encoder.encode([query])
        if not dense_vectors:
            return None
        return dense_vectors[0]

    def _semantic_score(
        self,
        query_semantic: object,
        semantic_norm: float,
        query_dense: list[float] | None,
        item: IndexedChunk,
    ) -> float:
        if query_dense is not None and item.dense_embedding is not None:
            return dense_dot_similarity(query_dense, item.dense_embedding)
        return cosine_similarity(
            query_semantic,  # type: ignore[arg-type]
            item.semantic_terms,
            semantic_norm,
            item.semantic_norm,
        )

    def _rerank(self, query: str, hits: list[SearchHit], top_k: int) -> list[SearchHit]:
        if not hits:
            return []
        candidate_count = max(top_k, self.rerank_candidate_pool)
        candidates = hits[:candidate_count]
        if self.reranker is None:
            return candidates[:top_k]

        rerank_scores = self.reranker.score_pairs(
            query, [candidate.chunk.text for candidate in candidates]
        )
        if rerank_scores is None:
            return candidates[:top_k]

        reranked_hits: list[SearchHit] = []
        for candidate, rerank_score in zip(candidates, rerank_scores):
            final_score = (
                (1.0 - self.rerank_weight) * candidate.score
                + self.rerank_weight * rerank_score
            )
            reranked_hits.append(
                SearchHit(
                    chunk=candidate.chunk,
                    score=final_score,
                    lexical_score=candidate.lexical_score,
                    semantic_score=candidate.semantic_score,
                    rerank_score=rerank_score,
                )
            )

        reranked_hits.sort(key=lambda hit: hit.score, reverse=True)
        return reranked_hits[:top_k]
