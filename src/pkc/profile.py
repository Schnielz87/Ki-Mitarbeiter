"""Mitarbeiterprofile (Masterprompt 53).

Ein Profil buendelt alles Fachliche eines KI-Mitarbeiters: Rolle,
Masterprompt, Faehigkeiten, Grenzen, Onboarding-Fragen, mitgelieferte
Fachmodule und Testfaelle.  Der technische Core kennt keinen einzigen
buchhaltungsspezifischen Begriff - ein neuer Mitarbeiter entsteht durch ein
neues Profilverzeichnis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .logging_setup import get_logger

log = get_logger(__name__)


@dataclass
class EmployeeProfile:
    profile_id: str
    name: str
    role: str
    version: str
    directory: Path
    system_prompt: str
    capabilities: list[str] = field(default_factory=list)
    limits: list[str] = field(default_factory=list)
    requires_approval: list[str] = field(default_factory=list)
    answer_sections: list[str] = field(default_factory=list)
    onboarding_keys: list[str] = field(default_factory=list)
    knowledge_modules: list[str] = field(default_factory=list)
    default_connectors: list[str] = field(default_factory=list)
    jurisdiction: str = ""
    disclaimer: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def knowledge_dir(self) -> Path:
        return self.directory / "knowledge"

    @property
    def short_name(self) -> str:
        return self.raw.get("short_name", self.name)

    def testcases_path(self) -> Path:
        return self.directory / "testcases.json"

    def summary(self) -> str:
        return (
            f"{self.name} (Profil {self.profile_id}, Version {self.version})\n"
            f"Rolle: {self.role}\n"
            f"Faehigkeiten: {len(self.capabilities)} · Grenzen: {len(self.limits)}"
        )


class ProfileError(RuntimeError):
    pass


def load_profile(profiles_dir: Path, profile_id: str) -> EmployeeProfile:
    directory = profiles_dir / profile_id
    config_file = directory / "profile.json"
    if not config_file.is_file():
        raise ProfileError(
            f"Mitarbeiterprofil '{profile_id}' nicht gefunden (erwartet: {config_file})."
        )
    data = json.loads(config_file.read_text(encoding="utf-8"))

    prompt_ref = data.get("system_prompt", "prompts/system.md")
    prompt_file = directory / prompt_ref
    if not prompt_file.is_file():
        raise ProfileError(f"Masterprompt des Profils fehlt: {prompt_file}")
    system_prompt = prompt_file.read_text(encoding="utf-8").strip()
    if len(system_prompt) < 200:
        raise ProfileError(f"Masterprompt {prompt_file} ist auffaellig kurz - bitte pruefen.")

    return EmployeeProfile(
        profile_id=data.get("profile_id", profile_id),
        name=data.get("name", profile_id),
        role=data.get("role", ""),
        version=data.get("version", "0"),
        directory=directory,
        system_prompt=system_prompt,
        capabilities=list(data.get("capabilities", [])),
        limits=list(data.get("limits", [])),
        requires_approval=list(data.get("requires_approval", [])),
        answer_sections=list(data.get("answer_sections", [])),
        onboarding_keys=list(data.get("onboarding_keys", [])),
        knowledge_modules=list(data.get("knowledge_modules", [])),
        default_connectors=list(data.get("default_connectors", [])),
        jurisdiction=data.get("jurisdiction", ""),
        disclaimer=data.get("disclaimer", ""),
        raw=data,
    )


def available_profiles(profiles_dir: Path) -> list[str]:
    if not profiles_dir.is_dir():
        return []
    return sorted(
        p.name for p in profiles_dir.iterdir()
        if p.is_dir() and (p / "profile.json").is_file()
    )
