from __future__ import annotations

from typing import Iterable, List

from app.core.types import Chunk, Document


class MarkdownChunker:
    def __init__(self, chunk_size: int = 520, overlap: int = 90) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: Iterable[Document]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for document in documents:
            chunks.extend(self.chunk_document(document))
        return chunks

    def chunk_document(self, document: Document) -> list[Chunk]:
        sections = self._split_into_sections(document.text)
        text_chunks: list[str] = []
        for section in sections:
            text_chunks.extend(self._pack_section(section))

        chunks: list[Chunk] = []
        for index, chunk_text in enumerate(text_chunks, start=1):
            chunk_id = f"{document.doc_id}-{index:04d}"
            chunks.append(
                Chunk(
                    doc_id=document.doc_id,
                    chunk_id=chunk_id,
                    source=document.source,
                    title=document.title,
                    text=chunk_text,
                    metadata=document.metadata,
                )
            )
        return chunks

    def _split_into_sections(self, text: str) -> list[str]:
        lines = text.splitlines()
        sections: list[str] = []
        buffer: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") and buffer and self._has_content(buffer):
                sections.append("\n".join(buffer).strip())
                buffer = [stripped]
            else:
                buffer.append(line)
        if buffer:
            sections.append("\n".join(buffer).strip())
        return [section for section in sections if section]

    def _has_content(self, lines: list[str]) -> bool:
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return True
        return False

    def _pack_section(self, section: str) -> List[str]:
        paragraphs = [part.strip() for part in section.split("\n\n") if part.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            candidate = paragraph if not current else f"{current}\n\n{paragraph}"
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = self._overlap_tail(current, paragraph)
            else:
                chunks.extend(self._slice_large_paragraph(paragraph))
                current = ""

        if current:
            chunks.append(current)
        return chunks

    def _slice_large_paragraph(self, paragraph: str) -> list[str]:
        slices: list[str] = []
        start = 0
        while start < len(paragraph):
            end = min(len(paragraph), start + self.chunk_size)
            slices.append(paragraph[start:end].strip())
            if end == len(paragraph):
                break
            start = max(0, end - self.overlap)
        return [item for item in slices if item]

    def _overlap_tail(self, previous_chunk: str, next_paragraph: str) -> str:
        tail = previous_chunk[-self.overlap :].strip()
        candidate = f"{tail}\n\n{next_paragraph}".strip() if tail else next_paragraph
        if len(candidate) <= self.chunk_size:
            return candidate
        return next_paragraph[: self.chunk_size].strip()
