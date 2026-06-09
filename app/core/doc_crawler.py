from __future__ import annotations

import json
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urldefrag

import httpx
from bs4 import BeautifulSoup


SKIP_TAGS = {"script", "style", "noscript", "svg", "img", "button", "form"}
BLOCK_TAGS = {"p", "li", "blockquote"}
HEADING_TAGS = {"h1", "h2", "h3", "h4"}
CODE_TAGS = {"pre", "code"}


@dataclass(frozen=True)
class DocSource:
    source_id: str
    topic: str
    label: str
    start_urls: list[str]
    allow_domains: list[str]
    max_pages: int = 4
    description: str = ""


@dataclass(frozen=True)
class CrawledDocument:
    source_id: str
    topic: str
    source_name: str
    source_url: str
    title: str
    markdown: str
    file_name: str


@dataclass(frozen=True)
class CrawlOutcome:
    source_id: str
    topic: str
    source_url: str
    file_name: str
    output_path: str
    action: str
    title: str


@dataclass(frozen=True)
class CrawlReport:
    source_id: str
    topic: str
    source_name: str
    created_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    outcomes: list[CrawlOutcome]
    errors: list[str]


def load_doc_sources(config_path: str | Path) -> list[DocSource]:
    raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
    sources: list[DocSource] = []
    for item in raw:
        sources.append(
            DocSource(
                source_id=item["source_id"],
                topic=item["topic"],
                label=item["label"],
                start_urls=item["start_urls"],
                allow_domains=item["allow_domains"],
                max_pages=item.get("max_pages", 4),
                description=item.get("description", ""),
            )
        )
    return sources


class OfficialDocsCrawler:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self.client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "DevDocsQA-Crawler/1.0 (+https://github.com/chilingche1111-blip/RAG)"
                )
            },
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "OfficialDocsCrawler":
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.close()

    def crawl_source(
        self,
        source: DocSource,
        output_root: str | Path,
        page_limit: int | None = None,
        incremental: bool = True,
    ) -> list[CrawledDocument]:
        report = self.crawl_source_report(
            source,
            output_root,
            page_limit=page_limit,
            incremental=incremental,
        )
        return [
            CrawledDocument(
                source_id=outcome.source_id,
                topic=outcome.topic,
                source_name=report.source_name,
                source_url=outcome.source_url,
                title=outcome.title,
                markdown=(Path(outcome.output_path).read_text(encoding="utf-8")),
                file_name=outcome.file_name,
            )
            for outcome in report.outcomes
            if outcome.action != "error"
        ]

    def crawl_source_report(
        self,
        source: DocSource,
        output_root: str | Path,
        page_limit: int | None = None,
        incremental: bool = True,
    ) -> CrawlReport:
        output_root = Path(output_root)
        visited: set[str] = set()
        queue = deque(normalize_url(url) for url in source.start_urls)
        queued: set[str] = set(queue)
        limit = page_limit or source.max_pages
        manifest = load_crawl_manifest(output_root)
        outcomes: list[CrawlOutcome] = []
        errors: list[str] = []
        counts = {"created": 0, "updated": 0, "skipped": 0}

        while queue and (counts["created"] + counts["updated"] + counts["skipped"]) < limit:
            current_url = queue.popleft()
            canonical_url = normalize_url(current_url)
            queued.discard(canonical_url)
            if canonical_url in visited:
                continue
            visited.add(canonical_url)

            try:
                response = self.client.get(canonical_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                title, markdown = extract_markdown_from_html(soup, canonical_url)
            except Exception as exc:
                errors.append(f"{canonical_url}: {exc}")
                continue

            if markdown.strip():
                file_name = slugify_url(canonical_url) + ".md"
                document = CrawledDocument(
                    source_id=source.source_id,
                    topic=source.topic,
                    source_name=source.label,
                    source_url=canonical_url,
                    title=title,
                    markdown=markdown,
                    file_name=file_name,
                )
                action, output_path = self._write_document(
                    output_root,
                    document,
                    manifest=manifest,
                    incremental=incremental,
                )
                counts[action] += 1
                outcomes.append(
                    CrawlOutcome(
                        source_id=source.source_id,
                        topic=source.topic,
                        source_url=canonical_url,
                        file_name=file_name,
                        output_path=str(output_path),
                        action=action,
                        title=title,
                    )
                )

            for link in extract_links(soup, canonical_url):
                normalized_link = normalize_url(link)
                if normalized_link in visited or normalized_link in queued:
                    continue
                if not is_allowed_link(normalized_link, source.allow_domains):
                    continue
                queue.append(normalized_link)
                queued.add(normalized_link)

        save_crawl_manifest(output_root, manifest)
        return CrawlReport(
            source_id=source.source_id,
            topic=source.topic,
            source_name=source.label,
            created_count=counts["created"],
            updated_count=counts["updated"],
            skipped_count=counts["skipped"],
            error_count=len(errors),
            outcomes=outcomes,
            errors=errors,
        )

    def _write_document(
        self,
        output_root: Path,
        document: CrawledDocument,
        manifest: dict[str, dict[str, str]],
        incremental: bool,
    ) -> tuple[str, Path]:
        topic_dir = output_root / document.topic
        topic_dir.mkdir(parents=True, exist_ok=True)
        rendered = render_crawled_document(document)
        output_path = topic_dir / document.file_name
        content_sha = sha256(rendered.encode("utf-8")).hexdigest()
        manifest_key = document.source_url
        existing = manifest.get(manifest_key, {})
        action = "updated" if output_path.exists() else "created"
        if (
            incremental
            and existing.get("content_sha256") == content_sha
            and output_path.exists()
        ):
            action = "skipped"
        else:
            output_path.write_text(rendered, encoding="utf-8")

        manifest[manifest_key] = {
            "source_id": document.source_id,
            "topic": document.topic,
            "file_name": document.file_name,
            "output_path": str(output_path),
            "title": document.title,
            "content_sha256": content_sha,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return action, output_path


def render_crawled_document(document: CrawledDocument) -> str:
    frontmatter = "\n".join(
            [
                "---",
                f"source_id: {document.source_id}",
                f"topic: {document.topic}",
                f"source_name: {document.source_name}",
                f"source_url: {document.source_url}",
                "---",
                "",
            ]
        )
    return frontmatter + document.markdown.strip() + "\n"


def load_crawl_manifest(output_root: str | Path) -> dict[str, dict[str, str]]:
    manifest_path = Path(output_root) / ".crawl_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): value
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, dict)
    }


def save_crawl_manifest(output_root: str | Path, manifest: dict[str, dict[str, str]]) -> None:
    manifest_path = Path(output_root) / ".crawl_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def extract_markdown_from_html(soup: BeautifulSoup, url: str) -> tuple[str, str]:
    title = extract_title(soup, url)
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.body
    )
    if main is None:
        return title, f"# {title}\n"

    for tag in main.find_all(SKIP_TAGS):
        tag.decompose()

    lines: list[str] = [f"# {title}", ""]
    for tag in main.find_all(HEADING_TAGS.union(BLOCK_TAGS).union(CODE_TAGS)):
        if tag.name in HEADING_TAGS:
            text = normalize_whitespace(tag.get_text(" ", strip=True))
            if not text:
                continue
            level = int(tag.name[1])
            lines.extend([("#" * min(level, 4)) + f" {text}", ""])
            continue

        if tag.name == "pre":
            code_text = tag.get_text("\n", strip=False).strip()
            if code_text:
                lines.extend(["```text", code_text, "```", ""])
            continue

        if tag.name == "code" and tag.parent and tag.parent.name == "pre":
            continue

        text = normalize_whitespace(tag.get_text(" ", strip=True))
        if text:
            lines.extend([text, ""])

    markdown = "\n".join(deduplicate_blank_lines(lines)).strip()
    return title, markdown or f"# {title}"


def extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue
        absolute = urljoin(base_url, href)
        links.append(absolute)
    return links


def is_allowed_link(url: str, allow_domains: Iterable[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".zip")):
        return False
    hostname = parsed.netloc.lower()
    return any(hostname == domain or hostname.endswith("." + domain) for domain in allow_domains)


def normalize_url(url: str) -> str:
    clean_url, _fragment = urldefrag(url)
    return clean_url.rstrip("/")


def extract_title(soup: BeautifulSoup, url: str) -> str:
    if soup.title and soup.title.text.strip():
        return normalize_whitespace(soup.title.text.strip())
    first_heading = soup.find(["h1", "h2"])
    if first_heading:
        text = normalize_whitespace(first_heading.get_text(" ", strip=True))
        if text:
            return text
    parsed = urlparse(url)
    tail = parsed.path.rstrip("/").split("/")[-1] or parsed.netloc
    return tail.replace("-", " ").replace("_", " ").title()


def slugify_url(url: str) -> str:
    parsed = urlparse(url)
    slug_base = f"{parsed.netloc}{parsed.path}".strip("/")
    slug_base = slug_base.replace("/", "-")
    slug_base = re.sub(r"[^a-zA-Z0-9-]+", "-", slug_base)
    slug_base = re.sub(r"-{2,}", "-", slug_base).strip("-")
    return slug_base.lower() or "document"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def deduplicate_blank_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line.strip()
        if blank and previous_blank:
            continue
        output.append(line)
        previous_blank = blank
    return output
