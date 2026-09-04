"""Einbettungen fuer die semantische Suche.

Zwei Wege, bewusst getrennt:

``HashingEmbedder``
    Vollstaendig offline, ohne Modell, ohne externe Abhaengigkeit.  Er bildet
    Wort- und Zeichen-n-Gramme per Hashing auf einen Vektor ab (Hashing-Trick
    mit Vorzeichen, danach L2-Normierung).  Das ist *keine* echte
    Satzsemantik, faengt aber Wortvarianten, Komposita und Tippfehler deutlich
    besser als reine Volltextsuche - und ist immer verfuegbar.

``LlamaEmbedder``
    Nutzt ein lokales GGUF-Einbettungsmodell ueber ``llama-cpp-python``, wenn
    vorhanden.  Liefert echte Semantik, benoetigt aber ein Modell auf der SSD.

Ist kein Modell da, faellt das System auf ``HashingEmbedder`` zurueck - der
Nutzer wird darueber informiert, es wird nichts vorgetaeuscht.
"""

from __future__ import annotations

import hashlib
import math
import re
import struct
from typing import Iterable, Protocol, Sequence

from ..logging_setup import get_logger

log = get_logger(__name__)

_TOKEN = re.compile(r"[a-zA-ZäöüÄÖÜß0-9§]+", re.UNICODE)

#: Sehr haeufige deutsche Woerter. Sie tragen keine Bedeutung, erzeugen aber
#: Scheinaehnlichkeit zwischen beliebigen Texten.
_COMMON = frozenset("""
der die das dem den des ein eine einen einer eines und oder aber auch ist sind
war waren wird werden wurde wurden kann koennen muss muessen darf duerfen soll
sollen hat haben hatte hatten mit von fuer auf bei im in an zu zur zum als aus
nach ueber unter vor durch gegen ohne um dass wenn weil damit sich es sie er
wir ihr ich man nicht nur noch schon bereits sowie bzw beim vom zum
""".split())


class EmbeddingProvider(Protocol):
    name: str
    dim: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def pack_vector(vector: Sequence[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


def unpack_vector(blob: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"<{dim}f", blob))


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Kosinusaehnlichkeit; Vektoren sind bereits L2-normiert (Norm 1)."""
    return sum(x * y for x, y in zip(a, b))


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "")]


class HashingEmbedder:
    """Deterministische, modellfreie Einbettung (Hashing-Trick).

    Merkmale: Einzelwoerter, Wortbigramme und Zeichen-4-Gramme.  Die
    Zeichen-n-Gramme sind fuer das Deutsche wichtig, weil sie Komposita wie
    "Vorsteuerabzug" mit "Vorsteuer" verbinden.
    """

    def __init__(self, dim: int = 512, char_ngram: int = 4):
        self.dim = int(dim)
        self.char_ngram = int(char_ngram)
        self.name = f"hashing-{self.dim}d"

    def _features(self, text: str) -> list[tuple[str, float]]:
        tokens = [t for t in tokenize(text) if t not in _COMMON and len(t) > 1]
        features: list[tuple[str, float]] = [(f"w:{t}", 1.0) for t in tokens]
        features += [
            (f"b:{tokens[i]}_{tokens[i + 1]}", 0.7) for i in range(len(tokens) - 1)
        ]
        n = self.char_ngram
        for token in tokens:
            if len(token) <= n:
                continue
            padded = f"^{token}$"
            features += [
                (f"c:{padded[i:i + n]}", 0.45) for i in range(len(padded) - n + 1)
            ]
        return features

    def embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for feature, weight in self._features(text):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "little")
            index = value % self.dim
            sign = 1.0 if (value >> 63) & 1 else -1.0
            vector[index] += sign * weight
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0.0:
            return vector
        return [v / norm for v in vector]

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]


class LlamaEmbedder:
    """Echte Einbettungen ueber ein lokales GGUF-Modell (llama-cpp-python)."""

    def __init__(self, model_path: str, n_ctx: int = 2048, threads: int = 0):
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as exc:  # pragma: no cover - optionale Abhaengigkeit
            raise RuntimeError(
                "llama-cpp-python ist nicht installiert; semantische Einbettung "
                "ueber ein lokales Modell steht nicht zur Verfuegung."
            ) from exc
        kwargs = {"model_path": model_path, "embedding": True, "n_ctx": n_ctx, "verbose": False}
        if threads:
            kwargs["n_threads"] = threads
        self._llama = Llama(**kwargs)
        probe = self._llama.create_embedding("test")
        vector = probe["data"][0]["embedding"]
        if vector and isinstance(vector[0], list):  # pooled je Token
            vector = vector[0]
        self.dim = len(vector)
        self.name = f"llama:{model_path.rsplit('/', 1)[-1]}"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            data = self._llama.create_embedding(text)["data"][0]["embedding"]
            if data and isinstance(data[0], list):
                # Token-Einbettungen -> Mittelwert
                length = len(data[0])
                pooled = [sum(row[i] for row in data) / len(data) for i in range(length)]
                data = pooled
            norm = math.sqrt(sum(v * v for v in data)) or 1.0
            out.append([v / norm for v in data])
        return out


def build_embedder(
    kind: str = "hashing", dim: int = 512, model_path: str | None = None,
    threads: int = 0,
) -> EmbeddingProvider | None:
    """Erzeugt den konfigurierten Embedder mit ehrlichem Rueckfall."""
    kind = (kind or "hashing").lower()
    if kind == "none":
        return None
    if kind == "llama":
        if not model_path:
            log.warning(
                "Einbettungsmodell 'llama' gewaehlt, aber kein Modellpfad gesetzt - "
                "verwende die modellfreie Hashing-Einbettung."
            )
            return HashingEmbedder(dim)
        try:
            return LlamaEmbedder(model_path, threads=threads)
        except RuntimeError as exc:
            log.warning("%s Verwende die modellfreie Hashing-Einbettung.", exc)
            return HashingEmbedder(dim)
    return HashingEmbedder(dim)
