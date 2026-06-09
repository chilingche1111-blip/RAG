from __future__ import annotations

from dataclasses import dataclass


def _to_vector_list(raw_vectors: object) -> list[list[float]]:
    if hasattr(raw_vectors, "tolist"):
        converted = raw_vectors.tolist()
        if converted and isinstance(converted[0], (int, float)):
            return [list(float(value) for value in converted)]
        return [list(float(value) for value in row) for row in converted]
    return [list(float(value) for value in row) for row in raw_vectors]  # type: ignore[arg-type]


@dataclass
class SentenceTransformerEncoder:
    model_name: str
    enabled: bool = True
    _model: object | None = None
    _status: str = "not_loaded"

    def encode(self, texts: list[str]) -> list[list[float]] | None:
        model = self._get_model()
        if model is None or not texts:
            return None
        raw_vectors = model.encode(  # type: ignore[call-arg]
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return _to_vector_list(raw_vectors)

    def backend_name(self) -> str:
        if self._status == "ready":
            return f"sentence-transformers:{self.model_name}"
        if not self.enabled:
            return "disabled"
        if self._status == "unavailable":
            return "fallback"
        return "lazy"

    def _get_model(self) -> object | None:
        if not self.enabled:
            self._status = "disabled"
            return None
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._status = "ready"
        except Exception:
            self._model = None
            self._status = "unavailable"
        return self._model


@dataclass
class CrossEncoderReranker:
    model_name: str
    enabled: bool = True
    _model: object | None = None
    _status: str = "not_loaded"

    def score_pairs(self, query: str, texts: list[str]) -> list[float] | None:
        model = self._get_model()
        if model is None or not texts:
            return None
        pairs = [[query, text] for text in texts]
        raw_scores = model.predict(pairs, show_progress_bar=False)  # type: ignore[call-arg]
        if hasattr(raw_scores, "tolist"):
            converted = raw_scores.tolist()
            return [float(item) for item in converted]
        return [float(item) for item in raw_scores]

    def backend_name(self) -> str:
        if self._status == "ready":
            return f"cross-encoder:{self.model_name}"
        if not self.enabled:
            return "disabled"
        if self._status == "unavailable":
            return "fallback"
        return "lazy"

    def _get_model(self) -> object | None:
        if not self.enabled:
            self._status = "disabled"
            return None
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
            self._status = "ready"
        except Exception:
            self._model = None
            self._status = "unavailable"
        return self._model
