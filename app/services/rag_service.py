from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from app.core.chunking import MarkdownChunker
from app.core.dense_models import CrossEncoderReranker, SentenceTransformerEncoder
from app.core.evaluation import EvalSummary, evaluate_cases, load_eval_cases
from app.core.generation import GroundedAnswerGenerator
from app.core.llm_generation import MultiProviderLLMGenerator
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
    query_log_limit: int = 40
    last_rebuild_at: str = ""
    recent_queries_buffer: deque[dict[str, str]] | None = None

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
        llm_provider: str = "openai",
        llm_model_name: str = "gpt-5.4-mini",
        llm_reasoning_effort: str = "minimal",
        llm_max_output_tokens: int = 420,
        llm_timeout_seconds: float = 30.0,
        llm_max_retries: int = 2,
        llm_retry_backoff_seconds: float = 1.0,
        query_log_limit: int = 40,
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
                llm_generator=MultiProviderLLMGenerator(
                    default_provider_id=llm_provider,
                    default_model_name=llm_model_name,
                    reasoning_effort=llm_reasoning_effort,
                    max_output_tokens=llm_max_output_tokens,
                    timeout_seconds=llm_timeout_seconds,
                    max_retries=llm_max_retries,
                    retry_backoff_seconds=llm_retry_backoff_seconds,
                    enabled=llm_enabled,
                )
            ),
            documents=[],
            query_log_limit=query_log_limit,
            recent_queries_buffer=deque(maxlen=query_log_limit),
        )
        service.rebuild()
        return service

    def rebuild(self, topics: Optional[list[str]] = None) -> dict[str, int | str]:
        normalized_topics = self._normalize_topics(topics)
        if not normalized_topics or not self.documents:
            self.documents = self._load_documents(self.knowledge_base_dir)
            chunks = self.chunker.chunk_documents(self.documents)
            self.retriever.build(chunks)
        else:
            replacement_documents = self._load_documents(
                self.knowledge_base_dir,
                topics=normalized_topics,
            )
            self.documents = [
                document
                for document in self.documents
                if self._document_topic(document.metadata) not in normalized_topics
            ]
            self.documents.extend(replacement_documents)
            self.documents.sort(key=lambda document: (self._document_topic(document.metadata), document.source))

            replacement_chunks: dict[str, list] = {topic: [] for topic in normalized_topics}
            for document in replacement_documents:
                topic = self._document_topic(document.metadata)
                replacement_chunks.setdefault(topic, []).extend(
                    self.chunker.chunk_document(document)
                )
            self.retriever.replace_topic_chunks(replacement_chunks)
        self.last_rebuild_at = datetime.now(timezone.utc).isoformat()
        return self.stats()

    def stats(self) -> dict[str, int | str]:
        topics = {self._document_topic(document.metadata) for document in self.documents}
        return {
            "document_count": len(self.documents),
            "chunk_count": self.retriever.chunk_count,
            "topic_count": len(topics),
            "knowledge_base_dir": str(self.knowledge_base_dir),
            "retrieval_backend": self.retriever.retrieval_backend,
            "reranker_backend": self.retriever.reranker_backend,
            "generation_backend": (
                self.generator.llm_generator.backend_name()
                if self.generator.llm_generator is not None
                else "extractive"
            ),
            "last_rebuild_at": self.last_rebuild_at,
            "query_log_size": len(self.recent_queries_buffer or []),
        }

    def query(
        self,
        question: str,
        top_k: int = 4,
        topic: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> QueryResult:
        metadata_filter = self._build_metadata_filter(topic)
        hits = self.retriever.search(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        result = self.generator.generate(
            question,
            hits,
            requested_topic=topic,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
        self._record_query(question, result)
        return result

    def llm_catalog(self) -> list[dict[str, str]]:
        if self.generator.llm_generator is None:
            return []
        return self.generator.llm_generator.provider_catalog()

    def llm_health_report(self) -> list[dict[str, object]]:
        if self.generator.llm_generator is None:
            return []
        return self.generator.llm_generator.provider_health_report()

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

    def recent_queries(self, limit: int = 20) -> list[dict[str, str]]:
        if self.recent_queries_buffer is None:
            return []
        return list(self.recent_queries_buffer)[:limit]

    def evaluate(
        self,
        eval_cases_path: Union[str, Path],
        top_k: int = 4,
        topic: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict[str, object]:
        cases = load_eval_cases(eval_cases_path)
        if topic:
            cases = [case for case in cases if (case.topic or "").lower() == topic.lower()]
        if limit is not None:
            cases = cases[:limit]
        summary: EvalSummary = evaluate_cases(
            self,
            cases,
            top_k=top_k,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
        return summary.to_dict()

    def _load_documents(
        self, directory: Path, topics: Optional[list[str]] = None
    ) -> list[Document]:
        documents: list[Document] = []
        if not directory.exists():
            return documents

        normalized_topics = self._normalize_topics(topics)
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            raw_text = path.read_text(encoding="utf-8")
            metadata, text = self._parse_frontmatter(path, raw_text)
            document_topic = self._document_topic(metadata)
            if normalized_topics and document_topic not in normalized_topics:
                continue
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

    def _normalize_topics(self, topics: Optional[list[str]]) -> list[str]:
        if not topics:
            return []
        normalized = sorted(
            {
                str(topic).strip().lower()
                for topic in topics
                if str(topic).strip()
            }
        )
        return normalized

    def _document_topic(self, metadata: dict[str, str]) -> str:
        return metadata.get("topic", "general").strip().lower() or "general"

    def _record_query(self, question: str, result: QueryResult) -> None:
        if self.recent_queries_buffer is None:
            return
        top_chunk_ids = ", ".join(hit.chunk.chunk_id for hit in result.hits[:2])
        self.recent_queries_buffer.appendleft(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "question": question,
                "topic": result.topic,
                "confidence_label": result.confidence_label,
                "answer_backend": result.answer_backend,
                "top_chunk_ids": top_chunk_ids,
            }
        )
