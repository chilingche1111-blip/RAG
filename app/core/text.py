from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
SPACE_PATTERN = re.compile(r"\s+")
MARKDOWN_PREFIX_PATTERN = re.compile(r"^\s{0,3}(#+|\-|\*|\d+\.)\s*")
MARKDOWN_HEADING_PATTERN = re.compile(r"^\s{0,3}#+\s*")


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    return SPACE_PATTERN.sub(" ", lowered)


def extract_lexical_terms(text: str) -> Counter[str]:
    terms: Counter[str] = Counter()
    for token in TOKEN_PATTERN.findall(normalize_text(text)):
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
            if len(token) == 1:
                terms[token] += 1
            else:
                for index in range(len(token) - 1):
                    terms[token[index : index + 2]] += 1
                for char in token:
                    terms[char] += 1
        else:
            terms[token] += 1
    return terms


def extract_semantic_terms(text: str, ngram_size: int = 3) -> Counter[str]:
    normalized = normalize_text(text).replace(" ", "")
    if not normalized:
        return Counter()
    if len(normalized) < ngram_size:
        return Counter({normalized: 1})
    return Counter(
        normalized[index : index + ngram_size]
        for index in range(len(normalized) - ngram_size + 1)
    )


def counter_norm(counter: Counter[str]) -> float:
    return math.sqrt(sum(value * value for value in counter.values()))


def cosine_similarity(
    left: Counter[str],
    right: Counter[str],
    left_norm: float | None = None,
    right_norm: float | None = None,
) -> float:
    if not left or not right:
        return 0.0
    left_norm = left_norm if left_norm is not None else counter_norm(left)
    right_norm = right_norm if right_norm is not None else counter_norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    dot_product = sum(value * right.get(token, 0) for token, value in left.items())
    return dot_product / (left_norm * right_norm)


def dense_dot_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(l_value * r_value for l_value, r_value in zip(left, right))


def sentence_split(text: str) -> list[str]:
    cleaned_lines = []
    for line in text.splitlines():
        if MARKDOWN_HEADING_PATTERN.match(line):
            continue
        cleaned = MARKDOWN_PREFIX_PATTERN.sub("", line).strip()
        if cleaned:
            cleaned_lines.append(cleaned)
    cleaned_text = "\n".join(cleaned_lines)
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", cleaned_text.strip())
    return [part.strip() for part in parts if part.strip()]


def best_matching_sentences(
    text: str, query_terms: Iterable[str], limit: int = 2
) -> list[str]:
    sentences = sentence_split(text)
    query_terms = list(query_terms)
    if not sentences:
        return []

    ranked = []
    for sentence in sentences:
        lexical_terms = extract_lexical_terms(sentence)
        score = sum(lexical_terms.get(term, 0) for term in query_terms)
        if len(sentence) < 8 and len(sentences) > 1:
            score -= 1
        ranked.append((score, len(sentence), sentence))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = [sentence for _, _, sentence in ranked[:limit] if sentence]
    return selected or sentences[:limit]
