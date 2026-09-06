"""Kopflose Steuerung der Anwendung.

Der Controller kennt keine Oberflaeche.  Die Tkinter-GUI und die
Kommandozeile sind beide nur Ansichten darauf - und die automatischen Tests
pruefen genau dieselbe Logik, die der Nutzer spaeter bedient.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from pkc.artefakte import Artefaktwerk, aus_markdown
from pkc.audit import ApprovalState, ApprovalStore, AuditLog
from pkc.checkpoint import CheckpointManager
from pkc.config import Config
from pkc.connectors import build_registry
from pkc.db import Database, utc_now
from pkc.db.schema import COMPANY_MIGRATIONS, KNOWLEDGE_MIGRATIONS
from pkc.hardware import HardwareInfo, PROFILES, detect, recommend_profile
from pkc.knowledge.bundled import ingest_bundled_modules
from pkc.knowledge.chunker import chunk_document
from pkc.knowledge.extract import ExtractionError, extract
from pkc.knowledge.store import KnowledgeStore
from pkc.licensing import LicenseChecker
from pkc.llm import tempo
from pkc.llm.base import ChatMessage
from pkc.llm.manager import LlmManager, discover_models
from pkc.logging_setup import get_logger, setup_logging
from pkc.memory import CaptureCandidate, MemoryCapture, MemoryStore
from pkc.memory.schema_keys import CATEGORIES, WELL_KNOWN_KEYS
from pkc.netstate import Betriebsart, Mode, NetworkMonitor, NetStatus
from pkc.paths import Paths, get_paths, sanitise_customer_id
from pkc.plugins import Pluginverwaltung
from pkc.profile import EmployeeProfile, load_profile
from pkc.rag import AnswerResult, ContextBuilder, RagEngine
from pkc.retrieval.embeddings import build_embedder
from pkc.retrieval.search import HybridSearcher, fts_query
from pkc.security import SecretVault, VaultError
from pkc.updater import HttpClient, SourceRegistry, UpdatePipeline
from pkc.updater.pipeline import UpdateReport

log = get_logger(__name__)


class LicenseRequired(RuntimeError):
    """Die produktive Nutzung verlangt eine gueltige Lizenz."""


@dataclass
class CheckItem:
    name: str
    ok: bool
    detail: str
    critical: bool = False

    @property
    def symbol(self) -> str:
        return "OK" if self.ok else ("FEHLER" if self.critical else "HINWEIS")


@dataclass
class StartupReport:
    """Ergebnis der Systempruefung beim Start (Masterprompt 38)."""

    items: list[CheckItem] = field(default_factory=list)
    mode: Mode = Mode.OFFLINE
    #: Der Netzbefund - getrennt von der Betriebsart. Beides gehoert in den
    #: Bericht: "OFFLINE gewaehlt, Internet verfuegbar" ist ein gueltiger
    #: und wichtiger Zustand.
    internet: bool = False
    knowledge_date: str | None = None
    hardware: HardwareInfo | None = None
    recommended_profile: str = "light"
    root: str = ""

    @property
    def usable(self) -> bool:
        return all(item.ok for item in self.items if item.critical)

    def add(self, name: str, ok: bool, detail: str, critical: bool = False) -> None:
        self.items.append(CheckItem(name, ok, detail, critical))

    def as_text(self, app_name: str = "PORTIVA") -> str:
        lines = [app_name.upper(), "", "Systempruefung", ""]
        width = max((len(i.name) for i in self.items), default=10)
        for item in self.items:
            lines.append(f"  {item.name.ljust(width)} : {item.symbol:7s} {item.detail}")
        lines += [
            "",
            f"  Wissensstand    : {self.knowledge_date or 'noch kein Wissen aufgenommen'}",
            f"  Internet        : {'verfuegbar' if self.internet else 'nicht verfuegbar'}",
            f"  Betriebsart     : {self.mode.value}",
            f"  Datenverzeichnis: {self.root}",
            "",
        ]
        lines.append(
            "  Der Buchhalter kann gestartet werden."
            if self.usable else
            "  ACHTUNG: Es liegt ein kritischer Fehler vor - bitte Hinweise oben lesen."
        )
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "einsatzbereit": self.usable,
            "betriebsart": self.mode.value,
            "internet": "verfuegbar" if self.internet else "nicht verfuegbar",
            "wissensstand": self.knowledge_date,
            "wurzel": self.root,
            "empfohlenes_profil": self.recommended_profile,
            "pruefungen": [
                {"name": i.name, "ok": i.ok, "detail": i.detail, "kritisch": i.critical}
                for i in self.items
            ],
            "hardware": self.hardware.as_dict() if self.hardware else None,
        }


@dataclass
class AskOutcome:
    """Ergebnis einer Frage inklusive moeglicher Gedaechtnis-Rueckfragen."""

    answer: AnswerResult
    conversation_uid: str
    message_id: int
    capture_candidates: list[CaptureCandidate] = field(default_factory=list)
    stored_automatically: list[str] = field(default_factory=list)


class AppController:
    """Baut die Anwendung auf und stellt alle Funktionen bereit."""

    def __init__(
        self,
        paths: Paths | None = None,
        config: Config | None = None,
        network: NetworkMonitor | None = None,
        console_logging: bool = True,
    ):
        self.paths = paths or get_paths()
        # Kundenbereich aus der Konfiguration uebernehmen, sofern noch nicht gesetzt
        if not self.paths.customer_id:
            vorkonfiguriert = str((config or Config.load(self.paths)).get("customer.id", ""))
            if vorkonfiguriert:
                self.paths = self.paths.for_customer(vorkonfiguriert)
        self.paths.ensure_runtime_dirs()
        self.paths.write_marker()
        self.config = config or Config.load(self.paths)
        setup_logging(
            self.paths.get("logs"),
            level=str(self.config.get("logging.level", "INFO")),
            max_bytes=int(self.config.get("logging.max_bytes", 2_000_000)),
            backups=int(self.config.get("logging.backups", 5)),
            console=console_logging,
        )
        log.info("Anwendung startet in %s", self.paths.root)

        # Profil
        self.profile: EmployeeProfile = load_profile(
            self.paths.get("profiles"), str(self.config.get("app.profile", "buchhalter"))
        )

        # Datenbanken
        self.knowledge_db = Database(self.paths.knowledge_db, KNOWLEDGE_MIGRATIONS)
        self.company_db = Database(self.paths.company_db, COMPANY_MIGRATIONS)
        self.knowledge = KnowledgeStore(self.knowledge_db)
        self.memory = MemoryStore(self.company_db)
        self.audit = AuditLog(self.company_db, bool(self.config.get("security.audit_enabled", True)))
        self.approvals = ApprovalStore(self.company_db, self.audit)

        # Recherche
        self.embedder = build_embedder(
            str(self.config.get("retrieval.embedding", "hashing")),
            int(self.config.get("retrieval.embedding_dim", 512)),
        )
        self.searcher = HybridSearcher(self.knowledge_db, self.embedder)
        self.capture = MemoryCapture(float(self.config.get("memory.min_confidence", 0.55)))

        # Lizenz (Masterprompt 84 bis 97)
        self.license = LicenseChecker(
            self.paths.program_root,
            product=str(self.config.get("license.product", "portabler-ki-mitarbeiter")),
            module=self.profile.profile_id,
            required=bool(self.config.get("license.required", False)),
        )
        self.license_status = self.license.check()

        # Marke und Profilname - getrennt gehalten (Masterprompt PORTIVA)
        from pkc.branding import load_brand, profilname as _profilname

        self.brand = load_brand(self.paths, self.config)
        self.profile_display_name = _profilname(self.profile)

        # Dateiausgabe (Erweiterung E4). Erzeugte Dateien sind Kundendaten
        # und liegen deshalb im Kundenbereich, nicht im Programmordner.
        self.artefakte = Artefaktwerk(
            self.paths, audit=self.audit, profil=self.profile_display_name,
            marke=self.brand.name,
        )

        # Plugins (Erweiterung E5). Geladen wird erst beim Start, damit ein
        # fehlerhaftes Plugin die Anwendung nicht am Hochfahren hindert.
        self.plugins = Pluginverwaltung(
            self.paths, config=self.config, audit=self.audit, memory=self.memory,
            knowledge=self.knowledge, artefakte=self.artefakte,
        )

        # Tresor
        self.vault = SecretVault(self.paths.secrets_file)

        # Sprachmodell
        self.llm = LlmManager.from_config(self.config, self.paths, self.vault.get_quiet)
        # Das Antworttempo bestimmt, wieviel Arbeit eine Antwort kosten darf.
        # Gemessen an einem echten Aufbau: 2712 Token Kontext und 1024
        # erlaubte Ausgabetoken sind der Grund, warum eine Antwort auf einem
        # Buerorechner Minuten dauert - nicht das Modell allein.
        tempowerte = tempo.stufe(self.config.get("llm.tempo", tempo.VORGABE))
        self.rag = RagEngine(
            self.profile, self.searcher, self.memory, self.llm,
            ContextBuilder(max_context_tokens=tempowerte["kontext_tokens"],
                           max_company_tokens=tempowerte["unternehmen_tokens"]),
            top_k=int(self.config.get("retrieval.top_k", 0) or tempowerte["top_k"]),
            lexical_candidates=int(self.config.get("retrieval.lexical_candidates", 40)),
            vector_candidates=int(self.config.get("retrieval.vector_candidates", 40)),
        )

        # Netz
        self.network = network or NetworkMonitor(
            self.config.get("network.probe_hosts", []),
            timeout=float(self.config.get("network.timeout_seconds", 4)),
            interval=float(self.config.get("network.check_interval_seconds", 60)),
            enabled=bool(self.config.get("network.check_on_start", True)),
        )

        # Betriebsmodus: die Wahl des Benutzers, getrennt vom Netzbefund.
        # Sie wird gespeichert und ueberlebt einen Neustart.
        self.betriebsart = Betriebsart(self.config, self.network)

        self._seed_default_config()

        # Aktualisierung
        self.registry: SourceRegistry | None = None
        self.registry_error = ""
        try:
            self.registry = SourceRegistry.load(self.paths.source_registry)
        except Exception as exc:
            self.registry_error = str(exc)
            log.warning("Quellenregister nicht nutzbar: %s", exc)
        self.updater: UpdatePipeline | None = None
        if self.registry is not None:
            self.updater = UpdatePipeline(
                self.paths, self.knowledge, self.registry, self.searcher,
                HttpClient(timeout=30.0),
                max_documents=int(self.config.get("updates.max_documents_per_run", 200)),
                chunk_tokens=int(self.config.get("retrieval.chunk_tokens", 400)),
                chunk_overlap=int(self.config.get("retrieval.chunk_overlap", 60)),
                config=self.config,
            )

        # Connectoren
        self.connectors = build_registry(
            self.config, self.approvals, self.audit, self.vault.get_quiet
        )
        self.checkpoints = CheckpointManager(self.paths.root)

        self.conversation_uid: str = ""
        self._bundled_result: dict = {}

    def _seed_default_config(self) -> list[str]:
        """Kopiert mitgelieferte Vorgabedateien in einen frischen Datenbereich.

        Notwendig, wenn Programm- und Datenbereich getrennt sind oder der
        Datenbereich neu angelegt wurde: das Quellenregister gehoert zum
        Lieferumfang, ist aber vom Nutzer aenderbar und liegt daher bei den
        Daten.
        """
        seeded: list[str] = []
        program_config = self.paths.program_root / "config"
        data_config = self.paths.get("config")
        if program_config.resolve() == data_config.resolve():
            return seeded
        # Der Modellkatalog gehoert genauso dazu: ohne ihn kaeme der
        # gefuehrte Weg zum Sprachmodell in einem frischen Datenbereich
        # nicht an seine Bezugsquellen.
        for name in ("source_registry.json", "model_catalog.json"):
            source = program_config / name
            target = data_config / name
            if source.is_file() and not target.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
                seeded.append(name)
                log.info("Vorgabedatei uebernommen: %s", name)
        return seeded

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------
    def bootstrap(self, ingest_modules: bool = True, build_embeddings: bool = True) -> StartupReport:
        """Systempruefung und Erstbefuellung. Idempotent."""
        report = StartupReport(root=str(self.paths.root))
        report.hardware = detect(self.paths.root)
        report.recommended_profile = recommend_profile(report.hardware)

        report.add(
            "Datenverzeichnis", self.paths.is_writable(),
            f"{self.paths.root} ({'beschreibbar' if self.paths.is_writable() else 'NICHT beschreibbar'})",
            critical=True,
        )
        healthy, detail = self.company_db.integrity_check()
        report.add("Unternehmensgedaechtnis", healthy,
                   f"{self.memory.stats()['active']} Eintraege, Integritaet: {detail}", critical=True)

        if ingest_modules:
            self._bundled_result = ingest_bundled_modules(
                self.knowledge, self.paths, self.profile.knowledge_dir, self.profile.profile_id,
                int(self.config.get("retrieval.chunk_tokens", 400)),
                int(self.config.get("retrieval.chunk_overlap", 60)),
            )
        stats = self.knowledge.stats()
        report.add(
            "Fachwissen", stats["documents"] > 0,
            f"{stats['documents']} Dokumente, {stats['chunks']} Abschnitte"
            + (f" (mitgelieferte Module: {self._bundled_result.get('gefunden', 0)})"
               if self._bundled_result else ""),
            critical=True,
        )

        if build_embeddings and self.embedder is not None:
            try:
                added = self.searcher.index_embeddings()
                report.add("Suchindex", True,
                           f"{stats['chunks']} Abschnitte, {added} Einbettungen ergaenzt "
                           f"({self.embedder.name})")
            except Exception as exc:
                report.add("Suchindex", False, f"Einbettungen fehlgeschlagen: {exc}")
        else:
            report.add("Suchindex", True, "Volltextsuche aktiv, semantische Suche deaktiviert")

        # Ein Notbetrieb ohne Modell ist KEIN "OK" - das waere Schoenfaerberei.
        from pkc.llm.providers import RetrievalOnlyProvider

        primary_ok, primary_detail = self.llm.primary.available()
        models = discover_models(self.paths.get("models"))
        has_model = primary_ok and not isinstance(self.llm.primary, RetrievalOnlyProvider)
        if has_model:
            detail = primary_detail
        else:
            reason = getattr(self.llm.primary, "reason", "") or primary_detail
            detail = (
                f"Kein Sprachmodell verfuegbar ({reason}). Die Anwendung laeuft im "
                f"Notbetrieb: sie recherchiert lokal, formuliert aber keine Fachantwort. "
                f"Gefundene Modelldateien in {self.paths.relative(self.paths.get('models'))}: "
                f"{len(models)}. Einrichtung: docs/MODELL_EINRICHTEN.md"
            )
        report.add("Lokales Modell", has_model, detail, critical=False)

        report.add(
            "Lizenz",
            self.license_status.productive_allowed,
            self.license_status.message,
            critical=self.license_status.required,
        )

        fehlend = self.brand.fehlende_dateien()
        report.add(
            "Branding", not fehlend,
            f"{self.brand.titel(self.profile_display_name)} · Logo und Symbole vorhanden"
            if not fehlend else
            f"{len(fehlend)} Brandingdatei(en) fehlen, u.a. {fehlend[0]}. "
            f"Die Anwendung laeuft; sie zeigt statt des Logos den Schriftzug. "
            f"Siehe assets/branding/original/HIER_ORIGINAL_ABLEGEN.md",
            critical=False,
        )

        report.add(
            "Quellenregister", self.registry is not None,
            f"{len(self.registry)} Quellen, {self.registry.document_count()} Dokumente"
            if self.registry else f"nicht ladbar: {self.registry_error}",
        )

        crypto_ok = True
        try:
            from pkc.security.vault import crypto_available
            crypto_ok, crypto_detail = crypto_available()
        except Exception as exc:  # pragma: no cover
            crypto_ok, crypto_detail = False, str(exc)
        report.add(
            "Geheimnistresor", True,
            (f"{'vorhanden' if self.vault.exists else 'noch nicht angelegt'} · {crypto_detail}")
            if crypto_ok else f"eingeschraenkt: {crypto_detail}",
        )

        # Plugins (Erweiterung E5). Ein fehlerhaftes Plugin schaltet sich
        # selbst ab und meldet den Grund - der Start geht weiter.
        plugins = self.plugins.laden(netz_erlaubt=self.lage.online_moeglich)
        fehlerhaft = [p for p in plugins if p.fehler]
        if plugins:
            report.add(
                "Plugins", not fehlerhaft,
                f"{len(plugins) - len(fehlerhaft)} aktiv"
                + (f" · ergaenzt: {', '.join(self.plugins.beitraege())}"
                   if self.plugins.beitraege() else " · ohne zusaetzliche Faehigkeit")
                + (f", {len(fehlerhaft)} abgeschaltet: {fehlerhaft[0].fehler}"
                   if fehlerhaft else ""),
                critical=False,
            )

        status = self.network.check()
        report.mode = self.mode          # die Wahl des Benutzers
        report.internet = status.online   # der Netzbefund
        report.knowledge_date = self.knowledge.knowledge_date()

        self.audit.record("start", "anwendung", "", status="ok" if report.usable else "fehler",
                          betriebsart=report.mode.value, wurzel=str(self.paths.root))

        # Zuletzt und im Hintergrund: das Modell laden, waehrend der Benutzer
        # sich im Fenster zurechtfindet. Blockiert den Start nicht und
        # verhindert, dass die erste Frage das Laden mit abwartet.
        self.modell_vorladen()
        return report

    def start_network_monitor(self) -> None:
        self.network.start()

    def shutdown(self) -> None:
        """Beendet die Anwendung geordnet.

        Mehrfach aufrufbar und auch dann unkritisch, wenn der Datenbereich
        inzwischen nicht mehr existiert - das Beenden darf nie der Grund fuer
        einen Absturz sein.
        """
        if getattr(self, "_beendet", False):
            return
        self._beendet = True

        # Zuerst auf den Vorladefaden warten. Wer die Anwendung schliesst,
        # waehrend das Modell noch laedt, wuerde sonst einen Modelldienst
        # zuruecklassen, der erst nach dem Beenden fertig hochkommt - genau
        # der verwaiste Vorgang, den es nicht geben darf. Der Faden prueft
        # das Kennzeichen selbst und steigt aus; die Frist ist nur die
        # Sicherung dagegen, dass das Fenster haengen bleibt.
        faden = getattr(self, "_vorladefaden", None)
        if faden is not None and faden.is_alive():
            log.info("Warte auf das Ende des Vorladens ...")
            faden.join(timeout=20.0)

        try:
            self.network.stop()
        except Exception:      # pragma: no cover - defensiv
            log.debug("Netzueberwachung liess sich nicht sauber beenden", exc_info=True)
        try:
            # Ein selbst gestarteter Modelldienst darf die Anwendung nicht
            # ueberleben - er haelt sonst still den Speicher des Modells.
            self.llm.beenden()
        except Exception:      # pragma: no cover - defensiv
            log.debug("Modelldienst liess sich nicht sauber beenden", exc_info=True)
        try:
            self.audit.record("beenden", "anwendung", "")
        except Exception:
            log.debug("Abschlusseintrag im Protokoll nicht moeglich", exc_info=True)
        for datenbank in (self.knowledge_db, self.company_db):
            try:
                datenbank.close()
            except Exception:  # pragma: no cover - defensiv
                log.debug("Datenbank liess sich nicht sauber schliessen", exc_info=True)

    # ------------------------------------------------------------------
    # Zustand
    # ------------------------------------------------------------------
    @property
    def mode(self) -> Mode:
        """Der **gewaehlte** Betriebsmodus - nicht der Netzbefund.

        Frueher wurde er aus dem Netzstatus abgeleitet. Damit waere OFFLINE
        keine Entscheidung, sondern nur die Beschreibung eines Zustands, und
        ein wiederkehrendes Netz haette den Benutzer unbemerkt zurueck in
        den Onlinebetrieb versetzt.
        """
        return self.betriebsart.modus

    @property
    def lage(self):
        """Betriebsmodus und Internetstatus nebeneinander."""
        return self.betriebsart.lage()

    def set_mode(self, modus, grund: str = "Benutzerwahl"):
        """Betriebsmodus wechseln, dauerhaft speichern und protokollieren."""
        self.betriebsart.audit = self.audit
        return self.betriebsart.waehlen(modus, grund)

    def versions(self) -> dict:
        """Alle Versionsangaben getrennt (Masterprompt 66).

        Ein spaeter gemeldeter Fehler muss einer konkreten Installation
        zugeordnet werden koennen - dafuer reicht eine einzelne Versionsnummer
        nicht aus.
        """
        profil_version = self.profile.version
        unternehmensprofil = int(self.company_db.scalar(
            "SELECT COALESCE(MAX(version), 0) FROM memory WHERE status='active'",
            default=0,
        ) or 0)
        return {
            # Marke und Profil wie im Fenstertitel (E1.11): die
            # Versionsauskunft soll dasselbe Produkt nennen wie die
            # Oberflaeche, nicht einen zweiten Namen.
            "produkt": self.brand.titel(self.profile_display_name),
            "softwareversion": str(self.config.get("product.version", "0.1.0")),
            "produktstufe": str(self.config.get("product.stage", "pilot")),
            "fachmodul": f"{self.profile.name} {profil_version}",
            "wissenspaket": str(self.config.get("product.knowledge_package", "-")),
            "wissensstand": self.knowledge.knowledge_date(),
            "unternehmensprofil": f"Version {unternehmensprofil}",
            "modell": self.llm.primary.model,
            "modell_anbieter": self.llm.primary.name,
            "instanz_id": self.license_status.instance_id,
            "lizenz": self.license_status.state.value,
        }

    def versions_text(self) -> str:
        felder = self.versions()
        breite = max(len(k) for k in felder)
        zeilen = [felder["produkt"], ""]
        for schluessel, wert in felder.items():
            if schluessel == "produkt":
                continue
            beschriftung = schluessel.replace("_", " ").capitalize()
            zeilen.append(f"  {beschriftung.ljust(breite)} : {wert}")
        return "\n".join(zeilen)

    def status(self) -> dict:
        knowledge = self.knowledge.stats()
        return {
            "anwendung": str(self.config.get("app.name", "Portabler Buchhalter")),
            "versionen": self.versions(),
            "lizenz": self.license_status.as_dict(),
            "profil": self.profile.name,
            "betriebsart": self.mode.value,
            "internet": "verfuegbar" if self.network.status.online else "nicht verfuegbar",
            "online_moeglich": self.lage.online_moeglich,
            "wissensstand": knowledge["knowledge_date"],
            "fachwissen": {"dokumente": knowledge["documents"], "abschnitte": knowledge["chunks"],
                           "einbettungen": knowledge["embeddings"], "quellen": knowledge["sources"]},
            "unternehmenswissen": self.memory.stats(),
            "modell": self.llm.status(),
            "wurzel": str(self.paths.root),
            "offene_freigaben": self.approvals.open_count(),
            "gespraeche": int(self.company_db.scalar(
                "SELECT COUNT(*) FROM conversations", default=0) or 0),
            "protokolleintraege": self.audit.count(),
            "connectoren": [i.as_dict() for i in self.connectors.info()],
        }

    def status_line(self) -> str:
        knowledge_date = self.knowledge.knowledge_date()
        date_text = knowledge_date[:10] if knowledge_date else "-"
        return (
            f"Betriebsart: {self.mode.value} · Wissensstand: {date_text} · "
            f"Modell: {self.llm.primary.model}"
        )

    # ------------------------------------------------------------------
    # Gespraeche
    # ------------------------------------------------------------------
    def new_conversation(self, title: str = "") -> str:
        uid = uuid.uuid4().hex[:16]
        now = utc_now()
        self.company_db.execute(
            "INSERT INTO conversations (uid, title, profile, created_at, updated_at)"
            " VALUES (?,?,?,?,?)",
            (uid, title or f"Unterhaltung vom {_dt.datetime.now():%d.%m.%Y %H:%M}",
             self.profile.profile_id, now, now),
        )
        self.conversation_uid = uid
        return uid

    def ensure_conversation(self) -> str:
        if not self.conversation_uid:
            self.new_conversation()
        return self.conversation_uid

    def conversations(self, limit: int = 100, include_archived: bool = False) -> list[dict]:
        sql = "SELECT * FROM conversations"
        if not include_archived:
            sql += " WHERE archived=0"
        sql += " ORDER BY updated_at DESC LIMIT ?"
        return [dict(r) for r in self.company_db.query(sql, (limit,))]

    def messages(self, conversation_uid: str = "", limit: int = 200) -> list[dict]:
        uid = conversation_uid or self.conversation_uid
        if not uid:
            return []
        rows = self.company_db.query(
            "SELECT m.* FROM messages m JOIN conversations c ON c.id=m.conversation_id "
            "WHERE c.uid=? ORDER BY m.id LIMIT ?",
            (uid, limit),
        )
        out = []
        for row in rows:
            item = dict(row)
            item["meta"] = json.loads(item.pop("meta_json") or "{}")
            item["sources"] = [
                dict(s) for s in self.company_db.query(
                    "SELECT * FROM message_sources WHERE message_id=? ORDER BY rank",
                    (row["id"],),
                )
            ]
            out.append(item)
        return out

    def open_conversation(self, uid: str) -> bool:
        exists = self.company_db.one("SELECT 1 FROM conversations WHERE uid=?", (uid,))
        if exists:
            self.conversation_uid = uid
            return True
        return False

    def archive_conversation(self, uid: str) -> bool:
        cursor = self.company_db.execute(
            "UPDATE conversations SET archived=1, updated_at=? WHERE uid=?", (utc_now(), uid)
        )
        return cursor.rowcount > 0

    def export_conversation(self, uid: str = "") -> Path:
        uid = uid or self.ensure_conversation()
        row = self.company_db.one("SELECT * FROM conversations WHERE uid=?", (uid,))
        if row is None:
            raise ValueError(f"Unterhaltung {uid} existiert nicht.")
        lines = [f"# {row['title']}", "", f"Angelegt: {row['created_at']}", ""]
        for message in self.messages(uid):
            who = {"user": "Frage", "assistant": "Antwort", "system": "System"}.get(
                message["role"], message["role"]
            )
            lines += [f"## {who} ({message['created_at']})", "", message["content"], ""]
        target = self.paths.get("conversations") / f"{uid}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines), encoding="utf-8")
        return target

    # ------------------------------------------------------------------
    # Sprachmodell einrichten (Erweiterung E6, Abschnitt 13 und 14)
    # ------------------------------------------------------------------
    def modell_katalog(self):
        """Die hinterlegten Bezugsquellen - mit Pruefstand je Eintrag."""
        from pkc.llm import katalog

        return katalog.laden(self.paths.get("config"))

    def modell_lage(self) -> dict:
        """Was ist da, was fehlt, und was waere der naechste Schritt?

        Diese eine Auskunft beantwortet die Frage, an der bisher jeder
        haengenblieb: warum sagt die Anwendung "kein Sprachmodell"?
        """
        from pkc.hardware import detect, recommend_profile
        from pkc.llm.manager import discover_models
        from pkc.llm.server import beschreibung, finde_server

        modelle = discover_models(self.paths.get("models"))
        programm = finde_server(self.paths.get("runtime"))
        hardware = detect(self.paths.root)
        profil = recommend_profile(hardware)
        katalog = self.modell_katalog()
        empfehlung = katalog.fuer_profil(profil)

        # "Bereit" heisst hier: ein Sprachmodell kann antworten. Der
        # Notbetrieb meldet sich selbst als verfuegbar - er ist es auch, aber
        # eben ohne Modell. Das als "bereit" auszugeben waere irrefuehrend.
        from pkc.llm.providers import RetrievalOnlyProvider

        bereit, hinweis = self.llm.primary.available()
        bereit = bereit and not isinstance(self.llm.primary, RetrievalOnlyProvider)
        fehlt: list[str] = []
        if not modelle:
            fehlt.append("die Modelldatei")
        if programm is None:
            fehlt.append("der Modelldienst (runtime/llama)")

        return {
            "modelle": [
                {"name": m.name, "groesse_gb": m.size_gb, "pfad": str(m.path)}
                for m in modelle
            ],
            "modellverzeichnis": str(self.paths.get("models")),
            "dienst": beschreibung(programm),
            "dienst_vorhanden": programm is not None,
            "anbieter": self.llm.primary.describe(),
            "bereit": bereit,
            "hinweis": hinweis,
            "fehlt": fehlt,
            "hardware": {
                "arbeitsspeicher_gb": hardware.ram_total_gb,
                "kerne": hardware.cpu_cores,
                "freier_platz_gb": hardware.free_disk_gb,
                "grafik": hardware.gpu_name,
            },
            "empfohlenes_profil": profil,
            "empfohlenes_profil_text": PROFILES.get(profil, {}).get("label", profil),
            "empfehlung": empfehlung.as_dict() if empfehlung else None,
            "katalog": [q.as_dict() for q in katalog],
            "katalogfehler": katalog.fehler,
        }

    def modell_beziehen(self, wunsch: str = "", *, bestaetigt: bool = False,
                        ueberschreiben: bool = False, fortschritt=None) -> dict:
        """Laedt ein Modell aus dem Katalog - nach ausdruecklicher Bestaetigung.

        Vier Sperren, die bewusst so sind:

        * Im Betriebsmodus OFFLINE wird nichts geladen.
        * Ohne Bestaetigung wird nichts geladen - es geht um mehrere Gigabyte
          und um Lizenzbedingungen, die der Betreiber kennen muss.
        * Ein Eintrag, dessen Adresse nie geprueft wurde, wird als solcher
          benannt (Masterprompt 42).
        * Reicht der Platz nicht, wird abgebrochen, bevor etwas beginnt.
        """
        from pkc.llm.bezug import laden

        katalog = self.modell_katalog()
        if not len(katalog):
            raise ValueError(katalog.fehler or "Der Modellkatalog ist leer.")

        quelle = katalog.waehlen(wunsch) if wunsch else None
        if quelle is None and not wunsch:
            from pkc.hardware import detect, recommend_profile

            quelle = katalog.fuer_profil(recommend_profile(detect(self.paths.root)))
        if quelle is None:
            moeglich = ", ".join(q.id for q in katalog)
            raise ValueError(f"Unbekannte Auswahl '{wunsch}'. Moeglich: {moeglich}")

        if self.mode is Mode.OFFLINE:
            raise ValueError(
                "Betriebsart OFFLINE: es wird nichts geladen. Fuer den Bezug "
                "eines Modells auf HYBRID oder ONLINE umschalten."
            )
        if not self.lage.online_moeglich:
            raise ValueError(
                "Zurzeit besteht keine Internetverbindung. Ein Modell laesst "
                "sich nur mit Verbindung beziehen - der uebrige Betrieb "
                "braucht sie nicht."
            )
        if not bestaetigt:
            raise ValueError(
                f"Vor dem Laden ist zu bestaetigen: {quelle.name}, etwa "
                f"{quelle.groesse_gb} GB, Lizenz {quelle.lizenz}. "
                f"Pruefstand der Bezugsquelle: {quelle.pruefstand}."
            )

        ziel = self.paths.get("models")
        ziel.mkdir(parents=True, exist_ok=True)
        frei_gb = shutil.disk_usage(ziel).free / 1024**3
        if frei_gb < quelle.groesse_gb * 1.1:
            raise ValueError(
                f"Auf dem Datentraeger sind nur {frei_gb:.1f} GB frei, "
                f"benoetigt werden etwa {quelle.groesse_gb} GB."
            )

        self.audit.record("modell_bezug", "modell", quelle.id, url=quelle.url,
                          geprueft=quelle.geprueft, teile=len(quelle.adressen))

        # Grosse Modelle kommen in Teilen. llama.cpp laedt sie ueber die
        # erste Datei, sofern alle danebenliegen - also muessen alle da sein,
        # bevor irgendetwas als fertig gilt.
        ergebnisse = []
        for nummer, adresse in enumerate(quelle.adressen, start=1):
            name = quelle.datei if len(quelle.adressen) == 1 else adresse.split("/")[-1]
            pruefsumme = quelle.sha256 if len(quelle.adressen) == 1 else ""
            ergebnis = laden(adresse, ziel, pruefsumme, name,
                             ueberschreiben=ueberschreiben, fortschritt=fortschritt)
            ergebnisse.append(ergebnis)
            if not ergebnis.ok:
                break

        letztes = ergebnisse[-1]
        vollstaendig = all(e.ok for e in ergebnisse)
        erste_datei = ergebnisse[0].pfad if ergebnisse and ergebnisse[0].pfad else None
        meldung = letztes.meldung
        if vollstaendig and len(ergebnisse) > 1:
            meldung = (f"{len(ergebnisse)} Teile geladen. Das Modell wird ueber "
                       f"{erste_datei.name if erste_datei else 'den ersten Teil'} "
                       "eingebunden; die uebrigen Teile muessen daneben liegen bleiben.")

        self.audit.record("modell_bezug_ende", "modell", quelle.id,
                          status="ok" if vollstaendig else "fehler",
                          meldung=meldung, teile=len(ergebnisse))
        return {
            "ok": vollstaendig,
            "quelle": quelle.as_dict(),
            "pfad": str(erste_datei) if erste_datei else "",
            "pruefsumme": ergebnisse[0].pruefsumme if ergebnisse else "",
            "meldung": meldung,
            "pruefsumme_vergleichbar": bool(quelle.sha256) and not quelle.geteilt,
            "bytes": sum(e.bytes_geladen for e in ergebnisse),
            "teile": len(ergebnisse),
        }

    def modell_uebernehmen(self, datei, *, ueberschreiben: bool = False,
                           fortschritt=None) -> dict:
        """Nimmt eine vorhandene Modelldatei auf - ohne sie neu zu laden.

        Das Modell gehoert auf den Datentraeger, nicht ins Netz. Wer es
        einmal hat, soll es nicht ein zweites Mal ziehen muessen: fuer einen
        weiteren Stick, fuer ein Buero mit gesperrtem Download, fuer eine
        Leitung, ueber die 4,7 GB nicht zweimal gehen.

        Hier wird nichts aus dem Internet geholt - der Betriebsmodus spielt
        deshalb keine Rolle, auch OFFLINE nicht.
        """
        from pkc.llm.bezug import uebernehmen

        quelle = Path(datei)
        self.audit.record("modell_uebernahme", "modell", quelle.name,
                          herkunft=str(quelle.parent))
        ergebnis = uebernehmen(quelle, self.paths.get("models"),
                               ueberschreiben=ueberschreiben,
                               fortschritt=fortschritt)
        self.audit.record("modell_uebernahme_ende", "modell", quelle.name,
                          status="ok" if ergebnis.ok else "fehler",
                          meldung=ergebnis.meldung)
        return {
            "ok": ergebnis.ok,
            "pfad": str(ergebnis.pfad) if ergebnis.pfad else "",
            "meldung": ergebnis.meldung,
            "pruefsumme": ergebnis.pruefsumme,
            "bytes": ergebnis.bytes_geladen,
        }

    def modell_vorladen(self) -> bool:
        """Faehrt den Modelldienst im Hintergrund hoch.

        Der groesste Einzelposten der Wartezeit auf die **erste** Antwort
        ist nicht das Rechnen, sondern das Laden des Modells: mehrere
        Gigabyte von der Platte. Geschieht das erst bei der ersten Frage,
        steht diese Zeit voll in ihrer Wartezeit.
        """
        anbieter = getattr(self.llm, "primary", None)
        vorladen = getattr(anbieter, "vorladen", None)
        if not callable(vorladen):
            return False
        if not self.config.get("llm.vorladen", True):
            return False

        import threading

        def vorbereiten() -> None:
            # Vor jedem Schritt nachsehen, ob die Anwendung inzwischen
            # beendet wurde. Sonst faehrt der Faden einen Dienst hoch, den
            # niemand mehr braucht und niemand mehr abschaltet.
            if getattr(self, "_beendet", False):
                return
            vorladen()
            if getattr(self, "_beendet", False):
                return
            self.modell_vorwaermen()

        faden = threading.Thread(target=vorbereiten, name="modell-vorladen",
                                 daemon=True)
        faden.start()
        self._vorladefaden = faden
        return True

    def modell_vorwaermen(self) -> bool:
        """Schickt den unveraenderlichen Kopf des Prompts einmal vorab.

        Der Modelldienst merkt sich den verarbeiteten Anfang eines Prompts.
        Beginnt der naechste Prompt genauso - und das tut er, der Kopf ist
        bei jeder Frage derselbe -, muss er ihn nicht erneut verarbeiten.

        Gemessen auf einem Windows-Rechner: die erste Frage brauchte 38 bis
        71 Sekunden bis zum ersten Wort, jede weitere 0,1 Sekunden. Genau
        dieser Unterschied ist der gemerkte Kopf. Ihn beim Start einmal
        vorab zu schicken heisst: auch die erste Frage ist schnell.

        Kostet nichts ausser der Zeit, in der der Benutzer ohnehin gerade das
        Fenster oeffnet. Schlaegt es fehl, bleibt es dabei - es ist eine
        Bequemlichkeit, kein Bestandteil der Antwort.
        """
        from pkc.rag.context import ContextBundle
        from pkc.rag.fragetyp import einstufen

        anbieter = getattr(self.llm, "primary", None)
        if anbieter is None or not getattr(anbieter, "name", "") or getattr(self, "_beendet", False):
            return False
        try:
            nachrichten = self.rag.build_messages(
                "Bereit?", ContextBundle(), mode=self.mode.value,
                knowledge_date=self.knowledge.knowledge_date(),
                einstufung=einstufen("Welche Pflichtangaben braucht eine Rechnung?"),
            )
            # Ein einziges Token Antwort. Es geht nicht um den Text, sondern
            # darum, dass der Dienst den Kopf einmal verarbeitet hat.
            self.llm.generate(nachrichten[:-1], max_tokens=1)
            log.info("Kopf des Prompts vorgewaermt")
            return True
        except Exception as fehler:               # pragma: no cover - defensiv
            log.info("Vorwaermen uebersprungen: %s", fehler)
            return False

    def modell_messen(self, frage: str = "", durchgaenge: int = 2) -> dict:
        """Misst die Wartezeit an einer echten Fachfrage - mehrfach.

        Zwei Durchgaenge, weil sie verschiedene Dinge messen. Der erste
        enthaelt das Laden des Modells und die vollstaendige Verarbeitung des
        Prompts. Beim zweiten steht der Dienst schon, und der unveraenderte
        Kopf des Prompts ist ihm bekannt - er muss nur noch verarbeiten, was
        sich geaendert hat.

        Der Unterschied zwischen beiden ist die Zahl, die zaehlt: so schnell
        ist die Anwendung im laufenden Betrieb.
        """
        import time as _time

        frage = frage or ("Welche Pflichtangaben braucht eine Rechnung nach "
                          "dem Umsatzsteuergesetz?")
        laeufe: list[dict] = []
        for nummer in range(1, max(int(durchgaenge), 1) + 1):
            erstes: list[float] = []
            begonnen = _time.monotonic()

            def zeichen(_stueck: str, _start=begonnen, _ziel=erstes) -> None:
                if not _ziel:
                    _ziel.append(_time.monotonic() - _start)

            try:
                ergebnis = self.ask(frage, on_token=zeichen, use_history=False)
            except Exception as fehler:
                laeufe.append({"nummer": nummer, "ok": False, "grund": str(fehler)})
                continue
            gesamt = _time.monotonic() - begonnen
            antwort = ergebnis.answer
            vom_modell = bool(antwort.model_answered)
            laeufe.append({
                "nummer": nummer,
                "ok": vom_modell,
                "erstes_wort_s": round(erstes[0] if erstes else 0.0, 1),
                "gesamt_s": round(gesamt, 1),
                "zeichen": len(antwort.text),
                "grund": "" if vom_modell else
                         "Es hat kein Sprachmodell geantwortet.",
            })

        gute = [l for l in laeufe if l.get("ok")]
        return {
            "ok": bool(gute),
            "frage": frage,
            "tempo": str(self.config.get("llm.tempo", tempo.VORGABE)),
            "laeufe": laeufe,
            # Der zweite Lauf ist der Alltag: Dienst laeuft, Kopf ist bekannt.
            "im_betrieb_erstes_wort_s": gute[-1]["erstes_wort_s"] if gute else 0.0,
            "im_betrieb_gesamt_s": gute[-1]["gesamt_s"] if gute else 0.0,
        }

    def tempo_anwenden(self) -> dict:
        """Uebernimmt das eingestellte Antworttempo in die laufende Anwendung.

        Kontextgroesse und Zahl der Fundstellen werden beim Aufbau der
        Recherche festgelegt. Ohne diesen Schritt wirkte eine Umstellung
        erst nach einem Neustart - der Benutzer haette also umgestellt,
        keine Aenderung bemerkt und die Einstellung fuer wirkungslos
        gehalten. Aufgefallen ist das erst, weil ein Test denselben Weg ging
        wie die Oberflaeche.
        """
        werte = tempo.stufe(self.config.get("llm.tempo", tempo.VORGABE))
        self.rag.builder = ContextBuilder(
            max_context_tokens=werte["kontext_tokens"],
            max_company_tokens=werte["unternehmen_tokens"])
        self.rag.top_k = int(self.config.get("retrieval.top_k", 0) or werte["top_k"])
        return werte

    def antwortlaenge(self) -> int:
        """Wieviele Token eine Antwort hoechstens haben darf.

        Ein ausdruecklich gesetzter Wert hat Vorrang; sonst kommt er aus dem
        Antworttempo. 1024 Token bei vier Token je Sekunde sind vier
        Minuten - das war die Vorgabe und der groesste Einzelposten.
        """
        ausdruecklich = int(self.config.get("llm.max_output_tokens", 0) or 0)
        if ausdruecklich > 0:
            return ausdruecklich
        return int(tempo.stufe(self.config.get("llm.tempo", tempo.VORGABE))
                   ["max_output_tokens"])

    def einrichtungsweg(self, text: str) -> None:
        """Sagt der Anwendung, wie der Benutzer das Modell einrichten kann.

        Fehlt das Modell, nennt die Antwort den Weg dorthin. Welcher Weg das
        ist, weiss nur die Bedienoberflaeche: wer im Fenster sitzt, soll
        nicht auf ein Konsolenprogramm verwiesen werden, das er erst suchen
        muss - und umgekehrt. Der Text wird gemerkt, damit er einen Neuaufbau
        der Modellanbindung ueberlebt.
        """
        self._einrichtungsweg = text
        self._weg_setzen()

    def _weg_setzen(self) -> None:
        from pkc.llm.providers import RetrievalOnlyProvider

        weg = getattr(self, "_einrichtungsweg", "")
        if not weg:
            return
        # Zwei Stellen, an denen der Notbetrieb entsteht: als eingerichteter
        # Anbieter (kein Modell gefunden) und als Rueckfall mitten in einer
        # Anfrage (alle Anbieter ausgefallen). Beide muessen denselben Weg
        # nennen, sonst haengt es vom Zufall ab, was der Benutzer liest.
        self.llm.einrichtungsweg = weg
        if isinstance(self.llm.primary, RetrievalOnlyProvider):
            self.llm.primary.weg = weg

    def modell_neu_laden(self) -> None:
        """Baut die Modellanbindung neu auf - nach einem Bezug noetig."""
        try:
            self.llm.beenden()
        except Exception:                        # pragma: no cover - defensiv
            log.debug("Alter Modelldienst liess sich nicht beenden", exc_info=True)
        self.llm = LlmManager.from_config(self.config, self.paths, self.vault.get_quiet)
        self.rag.llm = self.llm
        self._weg_setzen()

    def modell_probe(self, frage: str = "Antworte mit einem Satz: wofuer steht "
                                        "die Abkuerzung UStG?") -> dict:
        """Stellt dem Modell eine kleine Frage - der ehrliche Nachweis.

        Nicht "das Modell ist eingerichtet", sondern: es hat geantwortet,
        und zwar in dieser Zeit mit diesem Text.
        """
        import time as _time

        from pkc.llm.base import ChatMessage

        bereit, hinweis = self.llm.primary.available()
        if not bereit:
            return {"ok": False, "grund": hinweis, "anbieter": self.llm.primary.name}

        begonnen = _time.monotonic()
        try:
            antwort = self.llm.generate(
                [ChatMessage("system", "Antworte knapp auf Deutsch."),
                 ChatMessage("user", frage)],
                max_tokens=120,
                # Schrittweise, damit die Zeit bis zum **ersten** Wort
                # gemessen wird. Das ist die Wartezeit, die der Benutzer
                # erlebt - danach laeuft die Antwort sichtbar weiter.
                on_token=lambda _s: None,
            )
        except Exception as fehler:
            return {"ok": False, "grund": str(fehler), "anbieter": self.llm.primary.name}
        dauer = _time.monotonic() - begonnen

        # Der Strom liefert keine Tokenzahl mit; ueber die Zeichen laesst
        # sich die Groessenordnung aber verlaesslich schaetzen (im Deutschen
        # rund vier Zeichen je Token).
        token = antwort.completion_tokens or max(len(antwort.text) // 4, 1)
        erstes = antwort.erstes_token_s
        # Gemessen wird die Zeit des Anbieters, nicht die eigene Wanduhr:
        # sie beginnt mit dem Absenden und endet mit dem letzten Token. Ohne
        # diesen Bezug kann die Schreibzeit rechnerisch negativ werden - und
        # die Geschwindigkeit dann absurde Werte annehmen.
        gesamt = antwort.elapsed or dauer
        schreibzeit = gesamt - erstes
        if schreibzeit <= 0.01:
            schreibzeit = 0.0        # zu kurz zum Messen - lieber nichts sagen

        return {
            "ok": bool(antwort.is_generated and antwort.text.strip()),
            "anbieter": antwort.provider,
            "modell": antwort.model,
            "text": antwort.text.strip(),
            "dauer_s": round(gesamt, 1),
            # Die eigentliche Wartezeit: bis hierhin sieht der Benutzer nichts.
            "erstes_wort_s": round(erstes, 1),
            "token": token,
            "token_je_sekunde": (round(token / schreibzeit, 1) if schreibzeit else 0.0),
            "grund": "" if antwort.is_generated else "Es hat kein Sprachmodell geantwortet.",
        }

    # ------------------------------------------------------------------
    # Dateiausgabe (Erweiterung E4)
    # ------------------------------------------------------------------
    def artefakt_formate(self) -> list[dict]:
        """Welche Dateiformate erzeugt werden koennen."""
        return self.artefakte.formate()

    def artefakt_liste(self, limit: int = 50) -> list[dict]:
        return self.artefakte.liste(limit=limit)

    def datei_erzeugen(self, inhalt, format: str, name: str = "", *,
                       unterordner: str = "", ueberschreiben: bool = False,
                       angaben: dict | None = None):
        """Erzeugt eine Datei aus Text oder einem Dokument."""
        return self.artefakte.erzeugen(
            inhalt, format, name, unterordner=unterordner,
            ueberschreiben=ueberschreiben, angaben=angaben,
        )

    def antwort_speichern(self, format: str, conversation_uid: str = "",
                          name: str = "", ueberschreiben: bool = False):
        """Speichert die letzte Antwort der Unterhaltung als Datei.

        Gespeichert wird der Text, der auch im Fenster steht - mit
        Quellenteil und Wissensstand. Ein Bericht ohne diese Angaben waere
        nicht mehr nachvollziehbar.
        """
        uid = conversation_uid or self.conversation_uid
        antworten = [m for m in self.messages(uid) if m["role"] == "assistant"] if uid else []
        if not antworten:
            # Auf der Kommandozeile ist jede Ausfuehrung ein eigener Lauf. Ohne
            # diesen Rueckgriff liesse sich die Antwort, die eben noch auf dem
            # Bildschirm stand, nicht mehr speichern.
            letzte = self.company_db.one(
                "SELECT c.uid AS uid FROM messages m JOIN conversations c"
                " ON c.id = m.conversation_id WHERE m.role='assistant'"
                " ORDER BY m.id DESC LIMIT 1"
            )
            if letzte is not None:
                uid = letzte["uid"]
                antworten = [m for m in self.messages(uid) if m["role"] == "assistant"]
        if not antworten:
            raise ValueError("Es gibt noch keine Antwort, die gespeichert werden koennte.")
        letzte = antworten[-1]
        frage = ""
        for nachricht in self.messages(uid):
            if nachricht["role"] == "user":
                frage = nachricht["content"]
            if nachricht["id"] == letzte["id"]:
                break
        titel = (frage or "Antwort").strip().splitlines()[0][:70]
        dokument = aus_markdown(letzte["content"], titel=titel)
        dokument.angaben.update({
            "beschreibung": f"Antwort vom {letzte['created_at']}",
            "betriebsart": letzte.get("mode", ""),
        })
        return self.artefakte.erzeugen(
            dokument, format, name or titel, ueberschreiben=ueberschreiben,
        )

    def _store_message(
        self, conversation_uid: str, role: str, content: str,
        mode: str = "", model: str = "", meta: dict | None = None,
    ) -> int:
        row = self.company_db.one("SELECT id FROM conversations WHERE uid=?", (conversation_uid,))
        if row is None:
            raise ValueError(f"Unterhaltung {conversation_uid} existiert nicht.")
        now = utc_now()
        cursor = self.company_db.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at, mode, model, meta_json)"
            " VALUES (?,?,?,?,?,?,?)",
            (row["id"], role, content, now, mode, model,
             json.dumps(meta or {}, ensure_ascii=False)),
        )
        self.company_db.execute(
            "UPDATE conversations SET updated_at=? WHERE id=?", (now, row["id"])
        )
        return int(cursor.lastrowid)

    def _history(self, conversation_uid: str, turns: int = 6) -> list[ChatMessage]:
        rows = self.messages(conversation_uid)[-turns * 2:]
        return [
            ChatMessage(r["role"], r["content"])
            for r in rows if r["role"] in ("user", "assistant")
        ]

    # ------------------------------------------------------------------
    # Fragen beantworten
    # ------------------------------------------------------------------
    def ask(
        self,
        question: str,
        conversation_uid: str = "",
        as_of: str | None = None,
        use_history: bool = True,
        prefer_online: bool | None = None,
        on_token: Callable[[str], None] | None = None,
    ) -> AskOutcome:
        question = (question or "").strip()
        if not question:
            raise ValueError("Die Frage ist leer.")
        self.require_productive_use()
        uid = conversation_uid or self.ensure_conversation()
        lage = self.lage
        # Fuer die Antwort zaehlt, wie sie tatsaechlich zustande kam. Der
        # gewaehlte Modus allein waere irrefuehrend: HYBRID ohne Verbindung
        # ist fuer die Entstehung der Antwort dasselbe wie OFFLINE.
        mode = self.mode if lage.online_moeglich else Mode.OFFLINE
        knowledge_date = self.knowledge.knowledge_date()
        # Modellrouting nach Betriebsart (E6.12): OFFLINE ausschliesslich
        # lokal, HYBRID lokal als Grundfunktion, ONLINE darf ein freigegebenes
        # Online-Modell bevorzugen - sofern eines eingerichtet ist. Der
        # Aufrufer kann das ausdruecklich ueberstimmen.
        if prefer_online is None:
            prefer_online = mode is Mode.ONLINE

        self._store_message(uid, "user", question, mode.value)
        # Der Verlauf wandert bei jeder Frage erneut durch das Modell. Sechs
        # Zuege sind schnell einige tausend Token - also Wartezeit, bevor
        # das erste Wort erscheint.
        werte = tempo.stufe(self.config.get("llm.tempo", tempo.VORGABE))
        history = (self._history(uid, turns=werte["verlauf"] + 1)[:-1]
                   if use_history else [])

        result = self.rag.answer(
            question, history=history, mode=mode.value, knowledge_date=knowledge_date,
            as_of=as_of, max_tokens=self.antwortlaenge(),
            temperature=float(self.config.get("llm.temperature", 0.2)),
            prefer_online=prefer_online and lage.online_moeglich,
            on_token=on_token,
        )

        message_id = self._store_message(
            uid, "assistant", result.text, mode.value,
            result.llm.model if result.llm else "",
            meta={
                "anbieter": result.llm.provider if result.llm else "",
                "modellantwort": result.model_answered,
                "warnungen": result.warnings,
                "dauer_s": round(result.elapsed, 2),
            },
        )
        for rank, reference in enumerate(result.used_references or result.references, start=1):
            self.company_db.execute(
                "INSERT INTO message_sources (message_id, rank, origin, ref_id, citation,"
                " title, url, score, excerpt) VALUES (?,?,?,?,?,?,?,?,?)",
                (message_id, rank, reference.origin, reference.ref_id, reference.reference,
                 reference.title, reference.url, reference.score, reference.excerpt),
            )

        candidates: list[CaptureCandidate] = []
        stored: list[str] = []
        if bool(self.config.get("memory.auto_capture", True)):
            existing = [e.mem_key for e in self.memory.list(limit=500)]
            candidates = self.capture.analyse(question, existing)
            if not bool(self.config.get("memory.confirm_before_store", True)):
                for candidate in candidates:
                    self.remember(candidate, source=f"Chat {uid}")
                    stored.append(candidate.mem_key)
                candidates = []

        self.audit.record(
            "frage", "conversation", uid,
            modellantwort=result.model_answered, fundstellen=len(result.references),
            betriebsart=mode.value,
        )
        return AskOutcome(result, uid, message_id, candidates, stored)

    def require_productive_use(self) -> None:
        """Sperrt die produktive Nutzung ohne gueltige Lizenz (Masterprompt 87).

        Gesperrt wird ausschliesslich die *Nutzung*. Lizenzangaben ansehen,
        Unternehmenswissen einsehen und der Datenexport bleiben moeglich, und
        es werden keine Daten geloescht, gesperrt oder veraendert
        (Masterprompt 95).
        """
        if self.license_status.productive_allowed:
            return
        hinweise = "\n".join(f"  - {h}" for h in self.license_status.hints)
        raise LicenseRequired(
            f"{self.license_status.message}\n\n"
            "Die Anwendung laeuft eingeschraenkt weiter. Moeglich bleiben:\n"
            "  - Lizenzangaben ansehen (Befehl 'lizenz')\n"
            "  - Unternehmenswissen ansehen und exportieren (Befehl 'wissen')\n"
            "  - Sicherung erstellen (Befehl 'sicherung')\n"
            + (f"\n{hinweise}" if hinweise else "")
        )

    # ------------------------------------------------------------------
    # Unternehmensgedaechtnis
    # ------------------------------------------------------------------
    def remember(self, candidate: CaptureCandidate, source: str = "Chat") -> None:
        self.memory.put(
            candidate.mem_key, candidate.title, candidate.content, candidate.category,
            source=source, origin="agent", confidence=candidate.confidence,
            reason=candidate.rationale,
        )
        self.audit.record("wissen_gespeichert", "memory", candidate.mem_key,
                          kategorie=candidate.category, konfidenz=candidate.confidence)

    def remember_manual(
        self, mem_key: str, title: str, content: str, category: str = "other", **kwargs
    ):
        entry = self.memory.put(mem_key, title, content, category, **kwargs)
        self.audit.record("wissen_gespeichert", "memory", mem_key, kategorie=category)
        return entry

    def forget(self, mem_key: str, reason: str = "", hard: bool = False) -> bool:
        ok = self.memory.delete(mem_key, reason=reason, hard=hard)
        self.audit.record("wissen_geloescht" if hard else "wissen_archiviert",
                          "memory", mem_key, status="ok" if ok else "fehler", grund=reason)
        return ok

    def onboarding_questions(self) -> list[dict]:
        """Offene Punkte des Unternehmens-Onboardings (Masterprompt 39)."""
        questions = []
        for key in self.profile.onboarding_keys:
            meta = WELL_KNOWN_KEYS.get(key, {"category": "other", "title": key})
            entry = self.memory.get(key)
            questions.append({
                "key": key,
                "titel": meta["title"],
                "kategorie": meta["category"],
                "beantwortet": entry is not None,
                "wert": entry.content if entry else "",
            })
        return questions

    def onboarding_progress(self) -> tuple[int, int]:
        questions = self.onboarding_questions()
        return sum(1 for q in questions if q["beantwortet"]), len(questions)

    def answer_onboarding(self, key: str, value: str) -> None:
        meta = WELL_KNOWN_KEYS.get(key, {"category": "other", "title": key})
        self.memory.put(
            key, meta["title"], value.strip(), meta["category"],
            source="Onboarding", origin="onboarding",
        )
        self.audit.record("onboarding", "memory", key)

    def export_company_profile(self) -> Path:
        """Schreibt das Unternehmenswissen zusaetzlich menschenlesbar auf die SSD."""
        entries = self.memory.list(status="all", limit=100000)
        payload = {
            "exportiert_am": utc_now(),
            "profil": self.profile.profile_id,
            "eintraege": [e.as_dict() for e in entries],
        }
        target = self.paths.get("company") / "unternehmensprofil.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

        lines = ["# Unternehmensprofil", "", f"Stand: {utc_now()}", ""]
        by_category: dict[str, list] = {}
        for entry in entries:
            if entry.status != "active":
                continue
            by_category.setdefault(entry.category, []).append(entry)
        for category, items in sorted(by_category.items()):
            lines += [f"## {CATEGORIES.get(category, category)}", ""]
            for entry in items:
                lines.append(f"* **{entry.title}**: {entry.content}  ")
                lines.append(f"  _(Version {entry.version}, Stand {entry.updated_at[:10]})_")
            lines.append("")
        (self.paths.get("company") / "unternehmensprofil.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )
        return target

    # ------------------------------------------------------------------
    # Belege
    # ------------------------------------------------------------------
    def add_document(self, path: Path | str, title: str = "") -> dict:
        """Nimmt einen Beleg auf: Text extrahieren, indexieren, ablegen."""
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(f"Datei nicht gefunden: {source}")
        raw = source.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        doc_uid = f"BELEG_{digest[:16]}"

        existing = self.company_db.one("SELECT * FROM user_documents WHERE doc_uid=?", (doc_uid,))
        if existing is not None:
            return {"status": "bereits_vorhanden", "doc_uid": doc_uid,
                    "titel": existing["title"], "abschnitte": 0}

        target = self.paths.get("workspace") / "belege" / f"{doc_uid}{source.suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)

        try:
            document = extract(raw, "", "auto", source.name)
        except ExtractionError as exc:
            self.company_db.execute(
                "INSERT INTO user_documents (doc_uid, title, path, kind, sha256, bytes,"
                " added_at, status, meta_json) VALUES (?,?,?,?,?,?,?,?,?)",
                (doc_uid, title or source.name, self.paths.relative(target), source.suffix,
                 digest, len(raw), utc_now(), "nicht_lesbar",
                 json.dumps({"fehler": str(exc)}, ensure_ascii=False)),
            )
            return {"status": "nicht_lesbar", "doc_uid": doc_uid, "fehler": str(exc),
                    "titel": title or source.name, "abschnitte": 0}

        chunks = chunk_document(
            document, int(self.config.get("retrieval.chunk_tokens", 400)),
            int(self.config.get("retrieval.chunk_overlap", 60)),
        )
        cursor = self.company_db.execute(
            "INSERT INTO user_documents (doc_uid, title, path, kind, sha256, bytes,"
            " added_at, pages, status, meta_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (doc_uid, title or document.title or source.name, self.paths.relative(target),
             document.format, digest, len(raw), utc_now(),
             document.meta.get("pages"), "active",
             json.dumps({"quelle": str(source), "abschnitte": len(document.sections)},
                        ensure_ascii=False)),
        )
        doc_id = int(cursor.lastrowid)
        self.company_db.executemany(
            "INSERT INTO user_chunks (doc_id, ord, heading, text, tokens) VALUES (?,?,?,?,?)",
            [(doc_id, c.ord, c.heading, c.text, c.tokens) for c in chunks],
        )
        self.audit.record("beleg_hinzugefuegt", "document", doc_uid,
                          datei=source.name, abschnitte=len(chunks))
        return {"status": "aufgenommen", "doc_uid": doc_uid,
                "titel": title or document.title or source.name,
                "abschnitte": len(chunks), "pfad": self.paths.relative(target)}

    def documents(self, limit: int = 200) -> list[dict]:
        return [dict(r) for r in self.company_db.query(
            "SELECT * FROM user_documents WHERE status!='deleted' ORDER BY id DESC LIMIT ?",
            (limit,),
        )]

    def search_documents(self, query: str, limit: int = 5) -> list[dict]:
        expression = fts_query(query)
        if not expression:
            return []
        try:
            rows = self.company_db.query(
                """SELECT u.text, u.heading, d.title, d.doc_uid,
                          bm25(user_chunks_fts) AS score
                   FROM user_chunks_fts
                   JOIN user_chunks u ON u.id = user_chunks_fts.rowid
                   JOIN user_documents d ON d.id = u.doc_id
                   WHERE user_chunks_fts MATCH ? ORDER BY score LIMIT ?""",
                (expression, limit),
            )
        except Exception:  # pragma: no cover - defensiv
            return []
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Wissensupdate
    # ------------------------------------------------------------------
    def update_due(self) -> tuple[bool, str]:
        if self.updater is None:
            return False, f"Quellenregister nicht nutzbar: {self.registry_error}"
        return self.updater.due(
            str(self.config.get("updates.schedule", "manual")),
            int(self.config.get("updates.custom_interval_days", 14)),
        )

    def run_update(
        self, trigger: str = "manual", source_ids: Sequence[str] | None = None,
        dry_run: bool = False, progress: Callable[[str, int, int], None] | None = None,
        nur_faellige: bool = False,
    ) -> UpdateReport:
        """Fuehrt ein Wissensupdate durch.

        ``nur_faellige`` ist fuer den selbsttaetigen Lauf gedacht: dann
        werden nur Quellen abgerufen, deren Intervall abgelaufen ist
        (E2.20). Von Hand angestossen wird immer alles geprueft.
        """
        if self.updater is None:
            raise RuntimeError(f"Quellenregister nicht nutzbar: {self.registry_error}")
        status = self.network.check()
        report = self.updater.run(
            trigger=trigger, online=status.online, source_ids=source_ids,
            dry_run=dry_run, progress=progress, nur_faellige=nur_faellige,
        )
        self.audit.record("wissensupdate", "update", report.run_id, status=report.status,
                          aktualisiert=report.updated, fehlgeschlagen=report.failed)
        return report

    def update_faelligkeit(self):
        """Steht eine Wissensaktualisierung an? (Masterprompt-Ergaenzung 10-21)

        Beruecksichtigt den gewaehlten Betriebsmodus: im OFFLINE-Modus wird
        nicht synchronisiert, auch nicht bei bestehender Verbindung.
        """
        from pkc.updater.zeitplan import pruefen

        lage = self.lage
        return pruefen(
            self.config,
            self.knowledge.knowledge_date() or "",
            online_moeglich=lage.online_moeglich,
            modus_offline=self.mode is Mode.OFFLINE,
        )

    def rollback_update(self, run_id: str) -> tuple[bool, str]:
        if self.updater is None:
            return False, "Quellenregister nicht nutzbar."
        ok, message = self.updater.rollback(run_id)
        self.audit.record("wissensupdate_ruecknahme", "update", run_id,
                          status="ok" if ok else "fehler", meldung=message)
        return ok, message

    def update_runs(self, limit: int = 20) -> list[dict]:
        return self.updater.list_runs(limit) if self.updater else []

    # ------------------------------------------------------------------
    # Kundentrennung und Datenkontrolle (Masterprompt 61, 62)
    # ------------------------------------------------------------------
    @property
    def customer_id(self) -> str:
        return self.paths.customer_id

    def customers(self) -> list[dict]:
        """Alle Kundenbereiche auf diesem Datentraeger."""
        eintraege = []
        for kennung in self.paths.known_customers():
            bereich = self.paths.for_customer(kennung)
            datenbank = bereich.company_db
            eintraege.append({
                "kennung": kennung,
                "verzeichnis": self.paths.relative(bereich.customer_root),
                "angelegt": datenbank.is_file(),
                "groesse_bytes": datenbank.stat().st_size if datenbank.is_file() else 0,
                "aktiv": kennung == self.customer_id,
            })
        return eintraege

    def create_customer(self, customer_id: str, name: str = "") -> dict:
        """Legt einen neuen, leeren Kundenbereich an."""
        kennung = sanitise_customer_id(customer_id)
        if not kennung:
            raise ValueError("Es wurde keine Kundenkennung angegeben.")
        bereich = self.paths.for_customer(kennung)
        if bereich.customer_root.exists():
            raise ValueError(f"Der Kundenbereich '{kennung}' existiert bereits.")
        bereich.ensure_runtime_dirs()
        (bereich.customer_root / "KUNDE.txt").write_text(
            f"Kundenbereich: {kennung}\n"
            f"Name: {name or '(nicht angegeben)'}\n"
            f"Angelegt: {utc_now()}\n\n"
            "Dieser Ordner enthaelt ausschliesslich die Daten dieses Unternehmens.\n"
            "Das allgemeine Fachwissen liegt gemeinsam ausserhalb dieses Ordners.\n",
            encoding="utf-8",
        )
        self.audit.record("kunde_angelegt", "customer", kennung, name=name)
        log.info("Kundenbereich angelegt: %s", kennung)
        return {"kennung": kennung, "verzeichnis": self.paths.relative(bereich.customer_root)}

    def export_customer(self, target: Path | str | None = None) -> dict:
        """Exportiert alle Daten des aktiven Unternehmens (Masterprompt 62).

        Das Ergebnis ist ein eigenstaendiges Verzeichnis: Datenbanken,
        Unternehmensprofil, Gespraeche, Belege und Konfiguration. Es enthaelt
        **kein** Fachwissen und keine Lizenz.
        """
        stempel = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"export-{self.customer_id or 'einzelinstanz'}-{stempel}"
        ziel = Path(target) if target else (self.paths.get("backups") / name)
        ziel.mkdir(parents=True, exist_ok=True)

        self.export_company_profile()
        geschrieben: list[str] = []
        self.company_db.backup_to(ziel / "company.db")
        geschrieben.append("company.db")

        for verzeichnis in ("company", "conversations", "workspace"):
            quelle = self.paths.get(verzeichnis)
            if quelle.is_dir() and any(quelle.rglob("*")):
                shutil.copytree(quelle, ziel / verzeichnis, dirs_exist_ok=True)
                geschrieben.append(f"{verzeichnis}/")
        for datei in ("settings.json",):
            quelle = self.paths.get("config") / datei
            if quelle.is_file():
                (ziel / datei).write_bytes(quelle.read_bytes())
                geschrieben.append(datei)

        # Menschenlesbare Gesamtuebersicht des Unternehmenswissens
        (ziel / "unternehmenswissen.json").write_text(
            json.dumps(self.memory.export(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        geschrieben.append("unternehmenswissen.json")

        (ziel / "EXPORT.json").write_text(json.dumps({
            "kunde": self.customer_id or "einzelinstanz",
            "exportiert_am": utc_now(),
            "versionen": self.versions(),
            "dateien": geschrieben,
            "hinweis": "Enthaelt keine Lizenz und kein allgemeines Fachwissen.",
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        self.audit.record("kunde_exportiert", "customer", self.customer_id,
                          ziel=str(ziel), dateien=geschrieben)
        return {"verzeichnis": str(ziel), "dateien": geschrieben}

    def delete_conversation(self, uid: str, hard: bool = True) -> bool:
        """Loescht einen Gespraechsverlauf samt Nachrichten und Quellenbelegen."""
        zeile = self.company_db.one("SELECT id, title FROM conversations WHERE uid=?", (uid,))
        if zeile is None:
            return False
        if not hard:
            return self.archive_conversation(uid)
        with self.company_db.transaction():
            self.company_db.execute("DELETE FROM conversations WHERE uid=?", (uid,))
        export = self.paths.get("conversations") / f"{uid}.md"
        if export.is_file():
            export.unlink()
        if self.conversation_uid == uid:
            self.conversation_uid = ""
        self.audit.record("gespraech_geloescht", "conversation", uid, titel=zeile["title"])
        return True

    def delete_document(self, doc_uid: str) -> bool:
        """Loescht einen Beleg samt Text und abgelegter Datei."""
        zeile = self.company_db.one(
            "SELECT id, title, path FROM user_documents WHERE doc_uid=?", (doc_uid,)
        )
        if zeile is None:
            return False
        with self.company_db.transaction():
            self.company_db.execute("DELETE FROM user_documents WHERE doc_uid=?", (doc_uid,))
        datei = self.paths.root / zeile["path"]
        if datei.is_file():
            try:
                datei.unlink()
            except OSError as exc:      # pragma: no cover - Rechteproblem
                log.warning("Belegdatei nicht loeschbar: %s", exc)
        self.audit.record("beleg_geloescht", "document", doc_uid, titel=zeile["title"])
        return True

    def delete_customer(
        self, customer_id: str, confirm: str = "", export_first: bool = True
    ) -> dict:
        """Loescht einen kompletten Kundenbereich - bewusst schwer auszuloesen.

        Es muss die Kundenkennung ausdruecklich als Bestaetigung wiederholt
        werden. Vorher wird standardmaessig exportiert, damit ein Versehen
        nicht zum Totalverlust fuehrt.
        """
        kennung = sanitise_customer_id(customer_id)
        if not kennung:
            raise ValueError("Ohne Kundenkennung wird nichts geloescht.")
        if confirm != kennung:
            raise ValueError(
                f"Zur Bestaetigung muss die Kundenkennung '{kennung}' wiederholt werden."
            )
        bereich = self.paths.for_customer(kennung)
        if not bereich.customer_root.is_dir():
            raise ValueError(f"Der Kundenbereich '{kennung}' existiert nicht.")
        if kennung == self.customer_id:
            raise ValueError(
                "Der gerade geoeffnete Kundenbereich kann nicht geloescht werden. "
                "Bitte zuerst einen anderen Bereich oeffnen."
            )

        gesichert = None
        if export_first:
            fremd = AppController(
                bereich, Config.load(bereich), NetworkMonitor([], enabled=False),
                console_logging=False,
            )
            try:
                gesichert = fremd.export_customer(
                    self.paths.get("backups") / f"vor-loeschung-{kennung}"
                )["verzeichnis"]
            finally:
                fremd.shutdown()

        dateien = sum(1 for _ in bereich.customer_root.rglob("*") if _.is_file())
        shutil.rmtree(bereich.customer_root)
        self.audit.record("kunde_geloescht", "customer", kennung,
                          dateien=dateien, export=gesichert)
        log.warning("Kundenbereich geloescht: %s (%s Dateien)", kennung, dateien)
        return {"kennung": kennung, "geloeschte_dateien": dateien, "export": gesichert}

    # ------------------------------------------------------------------
    # Einstellungen und Sicherung
    # ------------------------------------------------------------------
    def save_settings(self, changes: dict[str, Any] | None = None) -> Path:
        for dotted, value in (changes or {}).items():
            self.config.set(dotted, value)
        target = self.config.save()
        self.audit.record("einstellungen", "config", str(target),
                          geaendert=list((changes or {}).keys()))
        return target

    def backup(self, label: str = "", target: Path | str | None = None) -> dict:
        """Sichert beide Datenbanken und die Konfiguration.

        ``target`` erlaubt ein **zweites Ziel** ausserhalb des Datentraegers
        (Masterprompt 75): eine zweite verschluesselte SSD, ein NAS oder ein
        freigegebener Unternehmensspeicher. Eine Sicherung, die nur auf
        demselben Datentraeger liegt, hilft bei dessen Verlust nicht.
        """
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"{stamp}-{label}" if label else stamp
        basis = Path(target) if target else self.paths.get("backups")
        directory = basis / name
        laufende_nummer = 1
        while directory.exists():
            laufende_nummer += 1
            directory = basis / f"{name}-{laufende_nummer}"
        directory.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        self.company_db.backup_to(directory / "company.db")
        written.append("company.db")
        self.knowledge_db.backup_to(directory / "knowledge.db")
        written.append("knowledge.db")
        for name in ("settings.json", "source_registry.json", "secrets.enc"):
            source = self.paths.get("config") / name
            if source.is_file():
                (directory / name).write_bytes(source.read_bytes())
                written.append(name)
        checksums = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.iterdir()) if path.is_file()
        }
        (directory / "MANIFEST.json").write_text(
            json.dumps({"erstellt_am": utc_now(), "dateien": written,
                        "pruefsummen": checksums}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.audit.record("sicherung", "backup", str(directory), dateien=written,
                          extern=bool(target))
        return {"verzeichnis": self.paths.relative(directory) if not target
                else str(directory),
                "pfad": str(directory), "extern": bool(target),
                "dateien": written, "pruefsummen": checksums}

    def setup_wizard_steps(self) -> list[dict]:
        """Gefuehrte Einrichtung eines neuen Unternehmens (Masterprompt 74).

        Nicht jeder Kunde darf durch individuelle Entwicklerarbeit eingerichtet
        werden muessen. Diese Schritte beschreiben den reproduzierbaren Weg und
        melden je Schritt, ob er bereits erledigt ist.
        """
        beantwortet, gesamt = self.onboarding_progress()
        modelle = discover_models(self.paths.get("models"))
        wissen = self.knowledge.stats()
        sicherungen = (
            [p for p in self.paths.get("backups").iterdir() if p.is_dir()]
            if self.paths.get("backups").is_dir() else []
        )
        return [
            {
                "nummer": 1, "schritt": "Portable KI installieren",
                "erledigt": self.paths.is_writable() and wissen["documents"] > 0,
                "hinweis": f"Datenverzeichnis {self.paths.root}, "
                           f"{wissen['documents']} Fachdokumente aufgenommen",
                "befehl": "check",
            },
            {
                "nummer": 2, "schritt": "Sprachmodell einrichten",
                "erledigt": bool(modelle),
                "hinweis": f"{len(modelle)} Modell(e) in "
                           f"{self.paths.relative(self.paths.get('models'))}"
                           if modelle else
                           "Kein Modell vorhanden - siehe docs/MODELL_EINRICHTEN.md",
                "befehl": "python tools/modell_einrichten.py empfehlen",
            },
            {
                "nummer": 3, "schritt": "Unternehmen anlegen",
                "erledigt": bool(self.customer_id) or bool(self.memory.get("company.name")),
                "hinweis": f"Kundenbereich '{self.customer_id}'" if self.customer_id
                           else "Einzelinstanz (fuer mehrere Unternehmen: kunde anlegen)",
                "befehl": "kunde anlegen <kennung> --name \"Firma\"",
            },
            {
                "nummer": 4, "schritt": "Onboarding durchfuehren",
                "erledigt": beantwortet >= max(5, gesamt // 3),
                "hinweis": f"{beantwortet} von {gesamt} Angaben beantwortet",
                "befehl": "onboarding --interaktiv",
            },
            {
                "nummer": 5, "schritt": "Fachregeln hinterlegen",
                "erledigt": self.memory.get("company.approval_rules") is not None,
                "hinweis": "Freigaberegeln und unternehmenseigene Vorgaben",
                "befehl": "wissen set company.approval_rules \"...\"",
            },
            {
                "nummer": 6, "schritt": "Connectoren einrichten (optional)",
                "erledigt": bool(self.connectors.configured_ids()),
                "hinweis": f"eingerichtet: {', '.join(self.connectors.configured_ids()) or 'keine'}",
                "befehl": "siehe ERP_CONNECTOR_KONZEPT.md",
            },
            {
                "nummer": 7, "schritt": "Sicherung einrichten",
                "erledigt": bool(sicherungen),
                "hinweis": f"{len(sicherungen)} Sicherung(en) vorhanden. Eine Kopie "
                           "gehoert auf ein zweites Ziel.",
                "befehl": "sicherung --ziel <pfad>",
            },
        ]

    def setup_progress(self) -> tuple[int, int]:
        schritte = self.setup_wizard_steps()
        return sum(1 for s in schritte if s["erledigt"]), len(schritte)

    def restore_info(self) -> dict:
        """Woran ein Nutzer den Projekt-/Datenstand erkennt (Masterprompt 45)."""
        backups = sorted(
            (p for p in self.paths.get("backups").iterdir() if p.is_dir()), reverse=True
        ) if self.paths.get("backups").is_dir() else []
        return {
            "wurzel": str(self.paths.root),
            "letzter_checkpoint": self.checkpoints.latest(),
            "sicherungen": [p.name for p in backups[:10]],
            "letzte_updatelaeufe": self.update_runs(5),
            "wissensstand": self.knowledge.knowledge_date(),
        }
