from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from app.core.chunking import MarkdownChunker
from app.core.dense_models import CrossEncoderReranker, SentenceTransformerEncoder
from app.core.generation import GroundedAnswerGenerator
from app.core.llm_generation import OpenAIResponseGenerator
from app.core.retrieval import HybridRetriever
from app.core.topic_catalog import list_topic_profiles
from app.core.types import Document, QueryResult


@dataclass
class RAGService:
    knowledge_base_dir: Path
    chunker: MarkdownChunker
    retriever: HybridRetriever
    generator: GroundedAnswerGenerator
    documents: list[Document]

    @classmethod
    def from_directory(
        cls,
        directory: Union[Path, str],
        chunk_size: int = 520,
        chunk_overlap: int = 90,
        min_score: float = 0.08,
        lexical_weight: float = 0.35,
        semantic_weight: float = 0.65,
        embedding_enabled: bool = True,
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        reranker_enabled: bool = True,
        reranker_model_name: str = "BAAI/bge-reranker-base",
        rerank_candidate_pool: int = 8,
        rerank_weight: float = 0.65,
        llm_enabled: bool = True,
        llm_model_name: str = "gpt-5.4-mini",
        llm_reasoning_effort: str = "minimal",
        llm_max_output_tokens: int = 420,
    ) -> "RAGService":
        directory = Path(directory)
        service = cls(
            knowledge_base_dir=directory,
            chunker=MarkdownChunker(chunk_size=chunk_size, overlap=chunk_overlap),
            retriever=HybridRetriever(
                lexical_weight=lexical_weight,
                semantic_weight=semantic_weight,
                min_score=min_score,
                embedding_encoder=SentenceTransformerEncoder(
                    model_name=embedding_model_name,
                    enabled=embedding_enabled,
                ),
                reranker=CrossEncoderReranker(
                    model_name=reranker_model_name,
                    enabled=reranker_enabled,
                ),
                rerank_candidate_pool=rerank_candidate_pool,
                rerank_weight=rerank_weight,
            ),
            generator=GroundedAnswerGenerator(
                llm_generator=OpenAIResponseGenerator(
                    model_name=llm_model_name,
                    reasoning_effort=llm_reasoning_effort,
                    max_output_tokens=llm_max_output_tokens,
                    enabled=llm_enabled,
                )
            ),
            documents=[],
        )
        service.rebuild()
        return service

    def rebuild(self) -> dict[str, int | str]:
        self.documents = self._load_documents(self.knowledge_base_dir)
        chunks = self.chunker.chunk_documents(self.documents)
        self.retriever.build(chunks)
        return self.stats()

    def stats(self) -> dict[str, int | str]:
        return {
            "document_count": len(self.documents),
            "chunk_count": self.retriever.chunk_count,
            "knowledge_base_dir": str(self.knowledge_base_dir),
            "retrieval_backend": self.retriever.retrieval_backend,
            "reranker_backend": self.retriever.reranker_backend,
            "generation_backend": (
                self.generator.llm_generator.backend_name()
                if self.generator.llm_generator is not None
                else "extractive"
            ),
        }

    def query(
        self,
        question: str,
        top_k: int = 4,
        topic: str | None = None,
    ) -> QueryResult:
        metadata_filter = self._build_metadata_filter(topic)
        hits = self.retriever.search(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        return self.generator.generate(
            question,
            hits,
            requested_topic=topic,
        )

    def topic_catalog(self) -> list[dict[str, str | list[str]]]:
        return [
            {
                "id": profile.id,
                "label": profile.label,
                "description": profile.description,
                "documentation_hint": profile.documentation_hint,
                "official_sources": profile.official_sources,
                "sample_questions": profile.sample_questions,
            }
            for profile in list_topic_profiles()
        ]

    def suggested_questions(self, topic: str | None = None) -> list[str]:
        topic = (topic or "").lower()
        for profile in list_topic_profiles():
            if not topic or profile.id == topic:
                return profile.sample_questions
        return [
            "FastAPI 依赖注入能解决什么问题？",
            "Redis 的 RDB 和 AOF 应该怎样取舍？",
            "为什么 Docker 某一层失效后后续层也会重建？",
        ]

    def _load_documents(self, directory: Path) -> list[Document]:
        documents: list[Document] = []
        if not directory.exists():
            return documents

        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            raw_text = path.read_text(encoding="utf-8")
            metadata, text = self._parse_frontmatter(path, raw_text)
            title = self._extract_title(path, text)
            doc_id = path.stem.replace(" ", "-").replace("_", "-").lower()
            documents.append(
                Document(
                    doc_id=doc_id,
                    title=title,
                    source=str(path),
                    text=text,
                    metadata=metadata,
                )
            )
        return documents

    def _extract_title(self, path: Path, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
        return path.stem.replace("_", " ").replace("-", " ").title()

    def _parse_frontmatter(self, path: Path, text: str) -> tuple[dict[str, str], str]:
        metadata: dict[str, str] = {"file_name": path.name}
        default_topic = path.parent.name.lower() if path.parent != self.knowledge_base_dir else "general"
        metadata["topic"] = default_topic
        metadata["source_name"] = path.stem.replace("-", " ").replace("_", " ").title()

        if not text.startswith("---\n"):
            return metadata, text

        closing_marker = text.find("\n---\n", 4)
        if closing_marker == -1:
            return metadata, text

        header = text[4:closing_marker]
        body = text[closing_marker + 5 :].lstrip()
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        return metadata, body

    def _build_metadata_filter(self, topic: str | None) -> dict[str, str] | None:
        metadata_filter: dict[str, str] = {}
        if topic:
            metadata_filter["topic"] = topic
        return metadata_filter or None
