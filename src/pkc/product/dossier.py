"""Lizenzregister, Bestandsliste und Release-Dossier (Masterprompt 63, 64, 73)."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import platform
from pathlib import Path

from ..db import utc_now
from .components import Component, collect_components, open_questions


def build_license_register(target: Path, components: list[Component] | None = None) -> Path:
    """Schreibt das Lizenzregister als lesbare Tabelle."""
    components = components or collect_components()
    zeilen = [
        "# Lizenzregister",
        "",
        f"Stand: {_dt.date.today().isoformat()} · erzeugt aus der tatsaechlich "
        "vorhandenen Installation",
        "",
        "Masterprompt 63 verlangt die Unterscheidung zwischen **Nutzung im eigenen",
        "Projekt** und **Weitergabe an Kunden**. Eine Komponente darf nicht deshalb",
        "in ein kommerzielles Produkt, weil sie kostenlos herunterladbar ist.",
        "",
        "> Diese Zusammenstellung ist die Arbeitsgrundlage fuer die rechtliche",
        "> Pruefung nach Masterprompt 71 - **nicht deren Ergebnis**. Sie ersetzt",
        "> keine Rechtsberatung.",
        "",
        "## Bestandteile",
        "",
        "| Komponente | Version | Herausgeber | Lizenz | Kommerziell | Weitergabe | Pflicht |",
        "|---|---|---|---|---|---|---|",
    ]
    for eintrag in components:
        zeilen.append(
            f"| {eintrag.name} | {eintrag.version} | {eintrag.vendor} | "
            f"{eintrag.licence} | {eintrag.commercial_use} | {eintrag.redistribution} | "
            f"{'ja' if eintrag.required else 'optional'} |"
        )

    zeilen += ["", "## Hinweise je Bestandteil", ""]
    for eintrag in components:
        zeilen += [
            f"### {eintrag.name}",
            "",
            f"* Zweck: {eintrag.purpose}",
            f"* Art: {eintrag.kind}",
            f"* Quelle: {eintrag.source}",
            f"* Geprueft am: {eintrag.checked}",
        ]
        if eintrag.notes:
            zeilen += ["", eintrag.notes]
        zeilen.append("")

    offen = open_questions(components)
    zeilen += ["## Vor einem Vertrieb zu klaeren", ""]
    if offen:
        zeilen += [f"{nummer}. {punkt}" for nummer, punkt in enumerate(offen, 1)]
    else:
        zeilen.append("Keine offenen Punkte erfasst.")
    zeilen += [
        "",
        "## Nicht enthalten",
        "",
        "Es werden keine kostenpflichtigen oder zugangsbeschraenkten Datenbanken",
        "kopiert. Das Unternehmensregister ist im Quellenregister deshalb",
        "ausdruecklich deaktiviert.",
        "",
    ]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(zeilen), encoding="utf-8")
    return target


def build_sbom(target: Path, product_version: str = "0.1.0",
               components: list[Component] | None = None) -> Path:
    """Bestandsliste im CycloneDX-Format (Masterprompt 64)."""
    components = components or collect_components()
    art = {"laufzeit": "framework", "bibliothek": "library", "werkzeug": "application",
           "modell": "machine-learning-model", "daten": "data"}
    dokument = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": utc_now(),
            "component": {
                "type": "application",
                "name": "portabler-ki-mitarbeiter",
                "version": product_version,
                "description": "Portabler KI-Mitarbeiter, Referenzimplementierung "
                               "KI-Buchhalter",
            },
            "tools": [{"name": "pkc.product.dossier", "version": product_version}],
            "properties": [
                {"name": "erzeugt_auf", "value": f"{platform.system()} {platform.machine()}"},
                {"name": "hinweis", "value": "Erzeugt aus der gepflegten Bestandsliste "
                                             "und den installierten Paketversionen."},
            ],
        },
        "components": [
            {
                "type": art.get(eintrag.kind, "library"),
                "name": eintrag.name,
                "version": eintrag.version,
                "publisher": eintrag.vendor,
                "description": eintrag.purpose,
                "scope": "required" if eintrag.required else "optional",
                "licenses": [{"license": {"name": eintrag.licence}}],
                "externalReferences": [{"type": "website", "url": eintrag.source}]
                if eintrag.source.startswith("http") else [],
                "properties": [
                    {"name": "kommerzielle_nutzung", "value": eintrag.commercial_use},
                    {"name": "weitergabe", "value": eintrag.redistribution},
                    {"name": "geprueft_am", "value": eintrag.checked},
                    {"name": "hinweis", "value": eintrag.notes},
                ],
            }
            for eintrag in components
        ],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dokument, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    return target


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(262144), b""):
            digest.update(block)
    return digest.hexdigest()


def build_release_dossier(
    project_root: Path,
    target: Path,
    version: str,
    test_summary: str = "",
    known_issues: list[str] | None = None,
    security_notes: list[str] | None = None,
    files_to_checksum: list[Path] | None = None,
) -> dict:
    """Erzeugt die Unterlagen zu einer veroeffentlichungsfaehigen Fassung.

    Masterprompt 73: Zu jeder Fassung muss spaeter nachvollziehbar sein, was
    sie enthielt, welche Tests sie bestanden hatte und welche Einschraenkungen
    bekannt waren.
    """
    target.mkdir(parents=True, exist_ok=True)
    geschrieben: list[str] = []

    def schreiben(name: str, inhalt: str) -> None:
        (target / name).write_text(inhalt, encoding="utf-8")
        geschrieben.append(name)

    schreiben("release_notes.md", "\n".join([
        f"# Portabler KI-Buchhalter {version}",
        "", f"Erstellt: {utc_now()}", "",
        "## Inhalt dieser Fassung", "",
        "Siehe CHANGELOG.md im Projektverzeichnis.", "",
        "## Bestandteile", "",
        "* `licenses.md` - Lizenzregister aller Bestandteile",
        "* `sbom.json` - Bestandsliste (CycloneDX)",
        "* `test_report.md` - Testergebnis dieser Fassung",
        "* `known_issues.md` - bekannte Einschraenkungen",
        "* `security_notes.md` - sicherheitsrelevante Hinweise",
        "* `checksums.txt` - Pruefsummen der Auslieferungsdateien",
        "",
    ]))

    schreiben("test_report.md", "\n".join([
        f"# Testergebnis {version}", "", f"Stand: {utc_now()}", "",
        test_summary or "Kein Testergebnis uebergeben - bitte nachtragen.", "",
        "Der ausfuehrliche Bericht steht in TESTBERICHT.md des Projekts.", "",
    ]))

    probleme = known_issues or []
    schreiben("known_issues.md", "\n".join([
        f"# Bekannte Einschraenkungen {version}", "", f"Stand: {utc_now()}", "",
        *([f"* {p}" for p in probleme] or ["* Keine erfasst."]), "",
        "Bekannte Einschraenkungen gehoeren zur Fassung. Sie werden bewusst",
        "aufgefuehrt, statt verschwiegen zu werden.", "",
    ]))

    hinweise = security_notes or []
    schreiben("security_notes.md", "\n".join([
        f"# Sicherheitshinweise {version}", "", f"Stand: {utc_now()}", "",
        *([f"* {h}" for h in hinweise] or ["* Keine besonderen Hinweise."]), "",
        "Das vollstaendige Konzept steht in SICHERHEITSKONZEPT.md.", "",
    ]))

    build_license_register(target / "licenses.md")
    geschrieben.append("licenses.md")
    build_sbom(target / "sbom.json", version)
    geschrieben.append("sbom.json")

    dateien = files_to_checksum or []
    zeilen = [f"{_sha256(p)}  {p.name}" for p in dateien if p.is_file()]
    schreiben("checksums.txt", "\n".join(zeilen) + ("\n" if zeilen else
              "# Keine Auslieferungsdateien uebergeben.\n"))

    return {"verzeichnis": str(target), "dateien": sorted(geschrieben),
            "pruefsummen": len(zeilen)}
