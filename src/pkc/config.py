"""Konfiguration des portablen KI-Mitarbeiters.

Kanonisches Format ist JSON (keine externe Abhaengigkeit noetig).  YAML wird
gelesen, wenn PyYAML vorhanden ist; benoetigt wird es nicht.

Die ausgelieferten Standardwerte stehen in ``DEFAULTS``.  Die Datei
``config/settings.json`` auf der SSD ueberschreibt sie punktuell (deep merge),
Umgebungsvariablen ``KIM_<PFAD_MIT_UNTERSTRICHEN>`` haben Vorrang.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

from .paths import Paths, get_paths

DEFAULTS: dict[str, Any] = {
    "app": {
        "name": "Portabler Buchhalter",
        "profile": "buchhalter",
        "language": "de",
        "version": "0.1.0",
    },
    "llm": {
        # "auto" waehlt das erste gefundene Modell in ./models
        "provider": "local",          # local | online | echo
        "model_path": "auto",
        "model_profile": "auto",      # auto | light | standard | high
        "context_tokens": 8192,
        "max_output_tokens": 1024,
        "temperature": 0.2,
        "threads": 0,                  # 0 = automatisch
        "gpu_layers": 0,
        "online": {
            "enabled": False,
            "base_url": "",
            "model": "",
            "secret_key": "online_llm_api_key",
        },
    },
    "retrieval": {
        "enabled": True,
        "top_k": 8,
        "lexical_candidates": 40,
        "vector_candidates": 40,
        "min_score": 0.0,
        "chunk_tokens": 400,
        "chunk_overlap": 60,
        "embedding": "hashing",       # hashing | llama | none
        "embedding_dim": 512,
    },
    "network": {
        "check_on_start": True,
        "check_interval_seconds": 60,
        "timeout_seconds": 4,
        "probe_hosts": [
            "https://www.gesetze-im-internet.de/",
            "https://www.bundesfinanzministerium.de/",
        ],
        "allow_online_llm": False,
        "allow_web_fetch": True,
    },
    "updates": {
        "schedule": "manual",          # manual | weekly | monthly | custom
        "custom_interval_days": 14,
        "max_documents_per_run": 200,
        "keep_reports": 50,
        "auto_start_check": False,
    },
    "memory": {
        "auto_capture": True,
        "confirm_before_store": True,
        "min_confidence": 0.55,
    },
    "security": {
        "vault_enabled": True,
        "require_passphrase_on_start": False,
        "audit_enabled": True,
    },
    "connectors": {
        "default_mode": "read_only",
        "enabled": [],
    },
    "ui": {
        "font_size": 11,
        "show_sources_panel": True,
        "theme": "light",
    },
    "logging": {
        "level": "INFO",
        "max_bytes": 2_000_000,
        "backups": 5,
    },
}


def deep_merge(base: dict, override: dict) -> dict:
    """Rekursives Zusammenfuehren zweier Dicts (override gewinnt)."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_mapping(path: Path) -> dict:
    """Laedt JSON oder (falls PyYAML vorhanden) YAML."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - optionale Abhaengigkeit
            raise RuntimeError(
                f"{path.name} benoetigt PyYAML. Bitte JSON verwenden."
            ) from exc
        return yaml.safe_load(text) or {}
    return json.loads(text) if text.strip() else {}


def _coerce(raw: str) -> Any:
    low = raw.strip().lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "none", ""):
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    if raw.strip().startswith(("[", "{")):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _env_overrides(data: dict, prefix: str = "KIM_") -> dict:
    """``KIM_LLM_PROVIDER=echo`` -> {"llm": {"provider": "echo"}}."""
    result = copy.deepcopy(data)
    reserved = {"KIM_ROOT", "KIM_CHECKPOINT_DIR", "KIM_PASSPHRASE"}
    for env_key, raw in os.environ.items():
        if not env_key.startswith(prefix) or env_key in reserved:
            continue
        parts = env_key[len(prefix):].lower().split("_")
        node: Any = result
        trail: list[tuple[dict, str]] = []
        matched: list[str] = []
        # gierige Aufloesung: laengste passende Schluessel zuerst
        idx = 0
        ok = True
        while idx < len(parts):
            if not isinstance(node, dict):
                ok = False
                break
            for span in range(len(parts) - idx, 0, -1):
                key = "_".join(parts[idx:idx + span])
                if key in node:
                    trail.append((node, key))
                    matched.append(key)
                    node = node[key]
                    idx += span
                    break
            else:
                ok = False
                break
        if not ok or not trail or isinstance(node, dict):
            continue
        parent, key = trail[-1]
        parent[key] = _coerce(raw)
    return result


class Config:
    """Geladene, zusammengefuehrte Konfiguration mit Punktzugriff."""

    def __init__(self, data: dict, paths: Paths, source: Path | None = None):
        self.data = data
        self.paths = paths
        self.source = source

    @classmethod
    def load(cls, paths: Paths | None = None) -> "Config":
        paths = paths or get_paths()
        merged = copy.deepcopy(DEFAULTS)
        source: Path | None = None
        for candidate in (
            paths.get("config") / "settings.json",
            paths.get("config") / "settings.yaml",
        ):
            if candidate.is_file():
                merged = deep_merge(merged, load_mapping(candidate))
                source = candidate
                break
        merged = _env_overrides(merged)
        return cls(merged, paths, source)

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        node = self.data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def save(self) -> Path:
        """Schreibt die *Abweichungen* zu den Defaults nach settings.json."""
        target = self.paths.settings_file
        target.parent.mkdir(parents=True, exist_ok=True)
        diff = _diff(DEFAULTS, self.data)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(diff, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        tmp.replace(target)
        self.source = target
        return target


def _diff(base: dict, current: dict) -> dict:
    out: dict[str, Any] = {}
    for key, value in current.items():
        if key not in base:
            out[key] = value
        elif isinstance(value, dict) and isinstance(base[key], dict):
            sub = _diff(base[key], value)
            if sub:
                out[key] = sub
        elif base[key] != value:
            out[key] = value
    return out
