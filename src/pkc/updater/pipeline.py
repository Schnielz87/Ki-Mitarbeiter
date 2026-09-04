"""Wissensupdate: Quelle -> Abruf -> Original -> Extraktion -> Normalisierung
-> Metadaten -> Chunking -> Index -> Bericht (Masterprompt 28 und 31).

Grundsaetze:
* **Inkrementell.**  ETag / Last-Modified / SHA-256 verhindern unnoetige
  Downloads und unnoetige Neuindexierung.
* **Ehrlich.**  Jeder Fehlschlag steht im Bericht.  Ein Lauf, in dem nichts
  geladen wurde, meldet das - er behauptet keinen Erfolg.
* **Rueckrollbar.**  Vor jedem Lauf wird die Wissensdatenbank gesichert; der
  Lauf kann vollstaendig zurueckgenommen werden.
* **Offline-Ergebnis.**  Nach dem Lauf ist das neue Wissen ohne Internet
  verfuegbar, weil Originale und Normalisate lokal liegen.
"""

from __future__ import annotations

import datetime as _dt
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from ..db import utc_now
from ..knowledge.chunker import chunk_document
from ..knowledge.extract import ExtractionError, extract
from ..knowledge.store import KnowledgeStore
from ..logging_setup import get_logger
from ..paths import Paths
from ..retrieval.search import HybridSearcher
from .http_client import HttpClient
from .registry import DocumentRef, Source, SourceRegistry

log = get_logger(__name__)

_EXTENSIONS = {
    "xml_zip": ".zip", "zip": ".zip", "xml": ".xml", "html": ".html",
    "pdf": ".pdf", "text": ".txt", "auto": ".bin",
}


@dataclass
class DocumentResult:
    doc_uid: str
    source_id: str
    title: str
    url: str
    status: str          # updated | unchanged | failed | skipped | new
    detail: str = ""
    chunks: int = 0
    bytes: int = 0
    sha256: str = ""
    elapsed: float = 0.0

    def as_dict(self) -> dict:
        return {
            "doc_uid": self.doc_uid, "source_id": self.source_id, "title": self.title,
            "url": self.url, "status": self.status, "detail": self.detail,
            "chunks": self.chunks, "bytes": self.bytes, "sha256": self.sha256[:16],
            "elapsed_s": round(self.elapsed, 2),
        }


@dataclass
class UpdateReport:
    run_id: str
    trigger: str
    started_at: str
    finished_at: str = ""
    status: str = "running"       # running|success|partial|failed|no_network|rolled_back
    results: list[DocumentResult] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    backup_path: str = ""
    embeddings_added: int = 0

    # -- Kennzahlen ----------------------------------------------------
    def count(self, status: str) -> int:
        return sum(1 for r in self.results if r.status == status)

    @property
    def checked(self) -> int:
        return len(self.results)

    @property
    def updated(self) -> int:
        return self.count("updated") + self.count("new")

    @property
    def unchanged(self) -> int:
        return self.count("unchanged")

    @property
    def failed(self) -> int:
        return self.count("failed")

    @property
    def skipped(self) -> int:
        return self.count("skipped")

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id, "trigger": self.trigger, "started_at": self.started_at,
            "finished_at": self.finished_at, "status": self.status,
            "summary": {
                "geprueft": self.checked, "aktualisiert": self.updated,
                "unveraendert": self.unchanged, "fehlgeschlagen": self.failed,
                "uebersprungen": self.skipped, "einbettungen_neu": self.embeddings_added,
            },
            "backup_path": self.backup_path,
            "messages": self.messages,
            "documents": [r.as_dict() for r in self.results],
        }

    def as_markdown(self) -> str:
        lines = [
            f"# Updatebericht {self.run_id}",
            "",
            f"* Ausloeser: **{self.trigger}**",
            f"* Beginn: {self.started_at}",
            f"* Ende: {self.finished_at or '-'}",
            f"* Ergebnis: **{self.status.upper()}**",
            "",
            "## Zusammenfassung",
            "",
            f"| geprueft | aktualisiert | unveraendert | fehlgeschlagen | uebersprungen |",
            f"|---:|---:|---:|---:|---:|",
            f"| {self.checked} | {self.updated} | {self.unchanged} | {self.failed} | {self.skipped} |",
            "",
        ]
        if self.messages:
            lines += ["## Hinweise", ""] + [f"* {m}" for m in self.messages] + [""]
        lines += ["## Dokumente", "", "| Status | Dokument | Quelle | Abschnitte | Detail |",
                  "|---|---|---|---:|---|"]
        for result in self.results:
            detail = result.detail.replace("|", "/")[:110]
            lines.append(
                f"| {result.status} | {result.title[:52]} | {result.source_id} "
                f"| {result.chunks} | {detail} |"
            )
        lines += ["", f"Sicherung fuer Ruecknahme: `{self.backup_path or '-'}`", ""]
        return "\n".join(lines)


class UpdatePipeline:
    """Fuehrt Wissensupdates durch - online wie im Trockenlauf."""

    def __init__(
        self,
        paths: Paths,
        store: KnowledgeStore,
        registry: SourceRegistry,
        searcher: HybridSearcher | None = None,
        client: HttpClient | None = None,
        max_documents: int = 200,
        chunk_tokens: int = 400,
        chunk_overlap: int = 60,
    ):
        self.paths = paths
        self.store = store
        self.registry = registry
        self.searcher = searcher
        self.client = client or HttpClient()
        self.max_documents = int(max_documents)
        self.chunk_tokens = int(chunk_tokens)
        self.chunk_overlap = int(chunk_overlap)

    # -- Planung -------------------------------------------------------
    def sync_sources(self) -> int:
        """Uebernimmt das Register in die Datenbank."""
        for source in self.registry:
            self.store.upsert_source(
                source.source_id, source.name, source.publisher, source.priority,
                source.kind, source.base_url, source.licence, source.enabled,
                {"fetcher": source.fetcher, "notes": source.notes, "verified": source.verified},
            )
        return len(self.registry.sources)

    def due(self, schedule: str, custom_days: int = 14) -> tuple[bool, str]:
        """Ist laut Zeitplan ein Update faellig?"""
        schedule = (schedule or "manual").lower()
        if schedule == "manual":
            return False, "Zeitplan 'manuell' - Update nur auf ausdrueckliche Anforderung."
        last = self.store.db.scalar(
            "SELECT MAX(finished_at) FROM update_runs WHERE status IN ('success','partial')"
        )
        if not last:
            return True, "Es wurde noch nie erfolgreich aktualisiert."
        try:
            last_dt = _dt.datetime.fromisoformat(last)
        except ValueError:
            return True, "Letzter Updatezeitpunkt nicht lesbar."
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=_dt.timezone.utc)
        days = {"weekly": 7, "monthly": 30}.get(schedule, max(1, int(custom_days)))
        age = (_dt.datetime.now(_dt.timezone.utc) - last_dt).days
        if age >= days:
            return True, f"Letztes Update vor {age} Tagen (Intervall {days} Tage)."
        return False, f"Letztes Update vor {age} Tagen - naechstes in {days - age} Tagen."

    # -- Durchfuehrung -------------------------------------------------
    def run(
        self,
        trigger: str = "manual",
        online: bool = True,
        source_ids: Sequence[str] | None = None,
        dry_run: bool = False,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> UpdateReport:
        run_id = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        report = UpdateReport(run_id=run_id, trigger=trigger, started_at=utc_now())
        run_dir = self.paths.get("updates") / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        if not online:
            report.status = "no_network"
            report.finished_at = utc_now()
            report.messages.append(
                "Kein Internetzugang - es wurde nichts abgerufen. "
                "Der lokale Wissensstand bleibt unveraendert nutzbar."
            )
            self._persist(report, run_dir)
            return report

        self.sync_sources()
        selected = [
            (source, doc)
            for source, doc in self.registry.all_documents()
            if source_ids is None or source.source_id in set(source_ids)
        ]
        if not selected:
            report.status = "failed"
            report.messages.append("Keine aktiven Quellen im Register ausgewaehlt.")
            report.finished_at = utc_now()
            self._persist(report, run_dir)
            return report

        if len(selected) > self.max_documents:
            report.messages.append(
                f"{len(selected)} Dokumente vorgesehen, Begrenzung auf {self.max_documents} "
                "je Lauf (siehe updates.max_documents_per_run)."
            )
            selected = selected[: self.max_documents]

        # Sicherung fuer Rollback
        if not dry_run:
            backup = run_dir / "knowledge.db.bak"
            try:
                self.store.db.backup_to(backup)
                report.backup_path = self.paths.relative(backup)
            except Exception as exc:  # pragma: no cover - defensiv
                report.messages.append(f"Sicherung vor dem Update fehlgeschlagen: {exc}")

        run_row = None
        if not dry_run:
            cursor = self.store.db.execute(
                "INSERT INTO update_runs (started_at, status, trigger) VALUES (?,?,?)",
                (report.started_at, "running", trigger),
            )
            run_row = cursor.lastrowid

        total = len(selected)
        per_source_ok: dict[str, bool] = {}
        for index, (source, doc) in enumerate(selected, start=1):
            if progress:
                progress(doc.title, index, total)
            result = self._process(source, doc, run_dir, dry_run)
            report.results.append(result)
            ok = result.status in ("updated", "new", "unchanged")
            per_source_ok[source.source_id] = per_source_ok.get(source.source_id, False) or ok

        if not dry_run:
            for source_id, ok in per_source_ok.items():
                errors = [
                    r.detail for r in report.results
                    if r.source_id == source_id and r.status == "failed"
                ]
                self.store.mark_source_checked(source_id, ok, errors[0] if errors else "")

        # Einbettungen nachziehen
        if self.searcher is not None and not dry_run and report.updated:
            try:
                report.embeddings_added = self.searcher.index_embeddings()
            except Exception as exc:  # pragma: no cover - defensiv
                report.messages.append(f"Einbettungen konnten nicht berechnet werden: {exc}")

        if report.failed == 0 and report.updated + report.unchanged > 0:
            report.status = "success"
        elif report.updated + report.unchanged > 0:
            report.status = "partial"
        else:
            report.status = "failed"
            report.messages.append(
                "Kein einziges Dokument konnte abgerufen werden. Der lokale Wissensstand "
                "wurde NICHT veraendert."
            )

        if not dry_run and report.updated:
            self.store.set_state("knowledge_date", utc_now())

        # Integritaetspruefung
        if not dry_run:
            healthy, detail = self.store.db.integrity_check()
            if not healthy:
                report.status = "failed"
                report.messages.append(f"Integritaetspruefung fehlgeschlagen: {detail}")
            else:
                report.messages.append("Integritaetspruefung der Wissensdatenbank: ok")

        report.finished_at = utc_now()
        paths_written = self._persist(report, run_dir)
        report.messages.append(f"Bericht: {self.paths.relative(paths_written[1])}")

        if not dry_run and run_row is not None:
            self.store.db.execute(
                """UPDATE update_runs SET finished_at=?, status=?, checked=?, downloaded=?,
                       updated=?, unchanged=?, failed=?, report_path=?, detail_json=?
                   WHERE id=?""",
                (report.finished_at, report.status, report.checked, report.updated,
                 report.updated, report.unchanged, report.failed,
                 self.paths.relative(paths_written[0]),
                 json.dumps({"messages": report.messages}, ensure_ascii=False), run_row),
            )
        self._prune_runs()
        return report

    # -- Ein Dokument --------------------------------------------------
    def _process(
        self, source: Source, doc: DocumentRef, run_dir: Path, dry_run: bool
    ) -> DocumentResult:
        result = DocumentResult(doc.doc_uid, source.source_id, doc.title, doc.url, "failed")
        etag, last_modified = self.store.cache_headers(doc.doc_uid)
        fetched = self.client.fetch(doc.url, etag=etag, last_modified=last_modified)
        result.elapsed = fetched.elapsed

        if fetched.not_modified:
            result.status = "unchanged"
            result.detail = "HTTP 304 - unveraendert"
            return result
        if not fetched.ok:
            result.detail = fetched.error or f"HTTP {fetched.status}"
            log.warning("Abruf fehlgeschlagen %s: %s", doc.url, result.detail)
            return result

        result.bytes = fetched.size
        result.sha256 = fetched.sha256
        existing = self.store.get_document(doc.doc_uid)
        if existing is not None and existing.sha256 == fetched.sha256:
            if not dry_run:
                self.store.upsert_document(
                    doc.doc_uid, source.source_id, existing.title, url=doc.url,
                    kind=doc.kind, citation=doc.citation, sha256=fetched.sha256,
                    size=fetched.size, etag=fetched.etag, last_modified=fetched.last_modified,
                    licence=doc.licence or source.licence, priority=source.priority,
                )
            result.status = "unchanged"
            result.detail = "inhaltsgleich (SHA-256 unveraendert)"
            return result

        try:
            document = extract(fetched.content, fetched.content_type, doc.format, doc.url)
        except ExtractionError as exc:
            result.detail = f"Extraktion fehlgeschlagen: {exc}"
            log.warning("%s: %s", doc.doc_uid, result.detail)
            return result

        chunks = chunk_document(document, self.chunk_tokens, self.chunk_overlap,
                                default_citation=doc.citation or document.title or doc.title)
        if not chunks:
            result.detail = "Dokument enthielt nach der Aufbereitung keine Abschnitte."
            return result
        result.chunks = len(chunks)

        if dry_run:
            result.status = "updated" if existing else "new"
            result.detail = "Trockenlauf - nichts geschrieben"
            return result

        raw_path = self._write_raw(source, doc, fetched.content)
        normalized_path = self._write_normalized(source, doc, document.text)
        metadata_path = self._write_metadata(source, doc, document, fetched, len(chunks))

        doc_id = self.store.upsert_document(
            doc.doc_uid, source.source_id, document.title or doc.title, url=doc.url,
            kind=doc.kind, citation=doc.citation,
            path_raw=self.paths.relative(raw_path),
            path_normalized=self.paths.relative(normalized_path),
            sha256=fetched.sha256, size=fetched.size, etag=fetched.etag,
            last_modified=fetched.last_modified, licence=doc.licence or source.licence,
            priority=source.priority,
            meta={
                "format": document.format, "sections": len(document.sections),
                "metadata_path": self.paths.relative(metadata_path),
                **document.meta,
            },
        )
        self.store.replace_chunks(doc_id, chunks)
        result.status = "new" if existing is None else "updated"
        result.detail = f"{len(document.sections)} Abschnitte, {len(chunks)} Chunks gespeichert"
        return result

    # -- Ablage --------------------------------------------------------
    def _write_raw(self, source: Source, doc: DocumentRef, content: bytes) -> Path:
        extension = _EXTENSIONS.get(doc.format, "")
        if not extension:
            extension = Path(doc.url.split("?", 1)[0]).suffix or ".bin"
        target = self.paths.get("resources_raw") / source.source_id / f"{doc.doc_uid}{extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def _write_normalized(self, source: Source, doc: DocumentRef, text: str) -> Path:
        target = self.paths.get("resources_normalized") / source.source_id / f"{doc.doc_uid}.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def _write_metadata(self, source, doc, document, fetched, chunk_count: int) -> Path:
        target = self.paths.get("resources_metadata") / source.source_id / f"{doc.doc_uid}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "doc_uid": doc.doc_uid,
            "title": document.title or doc.title,
            "citation": doc.citation,
            "source_id": source.source_id,
            "source_name": source.name,
            "publisher": source.publisher,
            "priority": source.priority,
            "priority_label": source.priority_label,
            "url": doc.url,
            "final_url": fetched.final_url,
            "licence": doc.licence or source.licence,
            "format": document.format,
            "sections": len(document.sections),
            "chunks": chunk_count,
            "sha256": fetched.sha256,
            "bytes": fetched.size,
            "etag": fetched.etag,
            "http_last_modified": fetched.last_modified,
            "fetched_at": utc_now(),
            "extraction_meta": document.meta,
        }
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return target

    def _persist(self, report: UpdateReport, run_dir: Path) -> tuple[Path, Path]:
        json_path = run_dir / "bericht.json"
        md_path = run_dir / "bericht.md"
        json_path.write_text(
            json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        md_path.write_text(report.as_markdown(), encoding="utf-8")
        return json_path, md_path

    def _prune_runs(self, keep: int = 50) -> None:
        base = self.paths.get("updates")
        runs = sorted((p for p in base.iterdir() if p.is_dir()), reverse=True)
        for stale in runs[keep:]:
            shutil.rmtree(stale, ignore_errors=True)

    # -- Ruecknahme ----------------------------------------------------
    def rollback(self, run_id: str) -> tuple[bool, str]:
        """Setzt die Wissensdatenbank auf den Stand vor dem Lauf zurueck."""
        backup = self.paths.get("updates") / run_id / "knowledge.db.bak"
        if not backup.is_file():
            return False, f"Keine Sicherung fuer Lauf {run_id} vorhanden."
        target = self.store.db.path
        self.store.db.close()
        safety = target.with_suffix(".db.before_rollback")
        try:
            if target.exists():
                shutil.copy2(target, safety)
            for suffix in ("-wal", "-shm"):
                side = Path(str(target) + suffix)
                if side.exists():
                    side.unlink()
            shutil.copy2(backup, target)
        except OSError as exc:
            return False, f"Ruecknahme fehlgeschlagen: {exc}"
        healthy, detail = self.store.db.integrity_check()
        if not healthy:
            return False, f"Zurueckgesetzte Datenbank ist nicht intakt: {detail}"
        self.store.db.execute(
            "UPDATE update_runs SET status='rolled_back' WHERE report_path LIKE ?",
            (f"%{run_id}%",),
        )
        log.warning("Wissensupdate %s zurueckgenommen", run_id)
        return True, f"Lauf {run_id} zurueckgenommen. Vorheriger Stand gesichert unter {safety.name}."

    def list_runs(self, limit: int = 20) -> list[dict]:
        return [
            dict(r) for r in self.store.db.query(
                "SELECT * FROM update_runs ORDER BY id DESC LIMIT ?", (limit,)
            )
        ]
