from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_name: str = "Developer Docs Intelligent QA"
    knowledge_base_dir: Path = Path(
        os.getenv("RAG_KB_DIR", "data/knowledge_base")
    )
    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "520"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "90"))
    default_top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    min_score: float = float(os.getenv("RAG_MIN_SCORE", "0.08"))
    lexical_weight: float = float(os.getenv("RAG_LEXICAL_WEIGHT", "0.35"))
    semantic_weight: float = float(os.getenv("RAG_SEMANTIC_WEIGHT", "0.65"))
    embedding_enabled: bool = os.getenv("RAG_ENABLE_EMBEDDINGS", "1") == "1"
    embedding_model_name: str = os.getenv(
        "RAG_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    reranker_enabled: bool = os.getenv("RAG_ENABLE_RERANKER", "1") == "1"
    reranker_model_name: str = os.getenv(
        "RAG_RERANKER_MODEL",
        "BAAI/bge-reranker-base",
    )
    rerank_candidate_pool: int = int(os.getenv("RAG_RERANK_CANDIDATES", "8"))
    rerank_weight: float = float(os.getenv("RAG_RERANK_WEIGHT", "0.65"))


settings = Settings()
