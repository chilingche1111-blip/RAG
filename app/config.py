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


settings = Settings()
