"""Kommandozeilenoberflaeche.

Sie ist bewusst vollwertig: fuer automatische Tests, fuer Rechner ohne
grafische Oberflaeche und als Notweg, falls die GUI einmal nicht startet.
Sie nutzt exakt denselben Controller wie die grafische Oberflaeche.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.controller import AppController, LicenseRequired
from pkc.artefakte import ArtefaktFehler
from pkc.plugins import SCHWERWIEGEND, PluginFehler
from pkc.audit import ApprovalState
from pkc.config import Config
from pkc.netstate import Mode
from pkc.paths import Paths, get_paths


def _controller(args) -> AppController:
    paths = Paths(Path(args.root).expanduser().resolve()) if args.root else get_paths()
    kunde = getattr(args, "kunde_bereich", "") or ""
    if kunde:
        paths = paths.for_customer(kunde)
    config = Config.load(paths)
    if args.offline:
        # --offline waehlt den Betriebsmodus fuer diesen Aufruf. Nur im
        # Arbeitsspeicher: ein einmaliger Schalter darf die dauerhaft
        # gespeicherte Wahl des Benutzers nicht ueberschreiben.
        config.set("network.mode", "OFFLINE")
        config.set("network.check_on_start", False)
    return AppController(paths, config, console_logging=not args.quiet)


def _print_report(report, controller=None) -> None:
    """Ueberschrift ist der Markentitel, z. B. ``PORTIVA - Buchhalter``."""
    titel = "PORTIVA"
    if controller is not None:
        titel = controller.brand.titel(controller.profile_display_name)
    print(report.as_text(titel))


def cmd_check(args) -> int:
    controller = _controller(args)
    try:
        report = controller.bootstrap()
        if args.json:
            print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
        else:
            _print_report(report, controller)
        return 0 if report.usable else 2
    finally:
        controller.shutdown()


def cmd_ask(args) -> int:
    controller = _controller(args)
    try:
        report = controller.bootstrap()
        if not report.usable:
            print(report.as_text(), file=sys.stderr)
            return 2
        try:
            outcome = controller.ask(args.frage, as_of=args.stand)
        except LicenseRequired as exc:
            print(str(exc), file=sys.stderr)
            return 4
        # Auch hier keine Markdown-Rohzeichen: in der Eingabeaufforderung
        # gibt es keinen Fettdruck, ** waere nur Zeichensalat.
        from ui.markdown import als_klartext

        print(als_klartext(outcome.answer.text))
        if outcome.capture_candidates:
            print("\n--- Moegliche dauerhafte Unternehmensinformation ---")
            for candidate in outcome.capture_candidates:
                print(f"  {candidate.question()}")
                print(f"    Schluessel: {candidate.mem_key} · Sicherheit: {candidate.confidence}")
                if args.merken:
                    controller.remember(candidate)
                    print("    -> gespeichert")
        return 0
    finally:
        controller.shutdown()


def cmd_chat(args) -> int:
    controller = _controller(args)
    try:
        report = controller.bootstrap()
        print(report.as_text())
        if not report.usable:
            return 2
        print("\nEingabe 'ende' beendet. 'status' zeigt die Lage.\n")
        while True:
            try:
                question = input("Sie > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question:
                continue
            if question.lower() in ("ende", "exit", "quit"):
                break
            if question.lower() == "status":
                print(json.dumps(controller.status(), indent=2, ensure_ascii=False))
                continue
            outcome = controller.ask(question)
            print(f"\nBuchhalter >\n{outcome.answer.text}\n")
            for candidate in outcome.capture_candidates:
                answer = input(f"  {candidate.question()} [j/N] ").strip().lower()
                if answer.startswith("j"):
                    controller.remember(candidate)
                    print("  -> dauerhaft gespeichert.")
        return 0
    finally:
        controller.shutdown()


def cmd_memory(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.action == "list":
            entries = controller.memory.list(category=args.kategorie, status=args.status)
            if not entries:
                print("Kein Unternehmenswissen gespeichert.")
            for entry in entries:
                print(f"  {entry.mem_key:38s} v{entry.version} [{entry.category}] {entry.title}")
                print(f"      {entry.content}")
        elif args.action == "set":
            entry = controller.remember_manual(
                args.key, args.titel or args.key, args.wert, args.kategorie or "other"
            )
            print(f"gespeichert: {entry.mem_key} (Version {entry.version})")
        elif args.action == "get":
            entry = controller.memory.get(args.key)
            print(entry.content if entry else "nicht vorhanden")
        elif args.action == "history":
            for item in controller.memory.history(args.key):
                print(f"  v{item['version']} {item['change_type']:8s} {item['changed_at']} "
                      f"- {item['snapshot']['content'][:70]}")
        elif args.action == "delete":
            print("archiviert" if controller.forget(args.key, hard=args.endgueltig)
                  else "nicht gefunden")
        elif args.action == "search":
            for entry in controller.memory.search(args.key):
                print(f"  [{entry.score:.2f}] {entry.title}: {entry.content}")
        elif args.action == "export":
            print(f"geschrieben: {controller.export_company_profile()}")
        return 0
    finally:
        controller.shutdown()


def cmd_update(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.zuruecknehmen:
            ok, message = controller.rollback_update(args.zuruecknehmen)
            print(message)
            return 0 if ok else 1

        def progress(title: str, index: int, total: int) -> None:
            print(f"  [{index}/{total}] {title[:60]}")

        report = controller.run_update(
            trigger="cli", source_ids=args.quelle or None, dry_run=args.trocken,
            progress=progress,
        )
        print(f"\nErgebnis: {report.status.upper()}")
        print(f"  geprueft {report.checked} · aktualisiert {report.updated} · "
              f"unveraendert {report.unchanged} · fehlgeschlagen {report.failed}")
        for message in report.messages:
            print(f"  - {message}")
        return 0 if report.status in ("success", "partial") else 1
    finally:
        controller.shutdown()


def cmd_recherche(args) -> int:
    """Zeigt die rohen Fundstellen zu einer Frage (Abschnitt 6).

    Rohtreffer sind technische Einzelheiten. Sie gehoeren nicht in die
    normale Antwort - wer sie sehen will, ruft sie ausdruecklich ab.
    """
    controller = _controller(args)
    try:
        controller.bootstrap()
        from pkc.rag.fragetyp import einstufen

        einstufung = einstufen(args.frage)
        print(f"Einstufung : {einstufung.typ.value}  ({einstufung.grund})")
        if not einstufung.braucht_recherche:
            print("Fuer diese Nachricht wird bewusst nicht recherchiert.")
            return 0

        treffer, eintraege = controller.rag.retrieve(args.frage)
        print(f"Fundstellen: {len(treffer)}\n")
        for nummer, hit in enumerate(treffer, start=1):
            print(f"[{nummer}] {hit.title or hit.reference or '(ohne Titel)'}")
            print(f"      Quelle    : {hit.source_id}")
            print(f"      Dokument  : {hit.doc_uid}")
            print(f"      Bewertung : {hit.score:.4f}")
            if getattr(hit, "url", ""):
                print(f"      Adresse   : {hit.url}")
            auszug = (hit.text or "").strip().replace("\n", " ")
            print(f"      Auszug    : {auszug[:200]}\n")
        if eintraege:
            print(f"Unternehmenswissen im Kontext: {len(eintraege)} Eintraege")
        return 0
    finally:
        controller.shutdown()


def cmd_datei(args) -> int:
    """Erzeugt eine Datei aus der letzten Antwort oder aus einem Text (E4).

    Der Auftrag verlangt, dass die Anwendung Arbeitsergebnisse nicht nur
    anzeigt, sondern als Datei herausgibt - offline und ohne installiertes
    Office.
    """
    controller = _controller(args)
    try:
        controller.bootstrap()
        if args.aktion == "formate":
            print("Diese Formate koennen erzeugt werden:\n")
            for eintrag in controller.artefakt_formate():
                print(f"  {eintrag['format']:5s} {eintrag['endung']:6s} "
                      f"{eintrag['bezeichnung']:28s} {eintrag['zweck']}")
            print(f"\nAblage: {controller.artefakte.ordner}")
            return 0

        if args.aktion == "liste":
            eintraege = controller.artefakt_liste()
            if not eintraege:
                print("Es wurde noch keine Datei erzeugt.")
                return 0
            for eintrag in eintraege:
                fehlt = "" if eintrag.get("vorhanden") else "  (Datei nicht mehr vorhanden)"
                print(f"{eintrag['erzeugt']}  {eintrag['format']:5s} "
                      f"{eintrag['pfad']}{fehlt}")
            return 0

        if args.aktion == "text":
            if not args.text:
                print("Bitte den Inhalt mit --text angeben.", file=sys.stderr)
                return 2
            artefakt = controller.datei_erzeugen(
                args.text, args.format, args.name,
                ueberschreiben=args.ueberschreiben,
            )
        else:                                   # antwort
            artefakt = controller.antwort_speichern(
                args.format, name=args.name, ueberschreiben=args.ueberschreiben,
            )
        print(f"Gespeichert: {artefakt.pfad}")
        print(f"  Format   : {artefakt.format}")
        print(f"  Fassung  : {artefakt.version}")
        print(f"  Groesse  : {artefakt.groesse} Bytes")
        print(f"  SHA-256  : {artefakt.pruefsumme}")
        return 0
    except (ValueError, ArtefaktFehler) as fehler:
        print(str(fehler), file=sys.stderr)
        return 1
    finally:
        controller.shutdown()


def cmd_plugin(args) -> int:
    """Plugins ansehen, pruefen, installieren, aktivieren, entfernen (E5).

    Die Reihenfolge ist die aus Abschnitt 123: pruefen, Berechtigungen zeigen,
    bestaetigen, installieren, aktivieren. Ohne Bestaetigung wird nichts
    installiert - ein Plugin laeuft mit den Rechten der Anwendung.
    """
    controller = _controller(args)
    try:
        controller.bootstrap()
        verwaltung = controller.plugins

        if args.aktion == "liste":
            staende = verwaltung.liste()
            if not staende:
                print("Es ist kein Plugin installiert.")
                print(f"Ablage fuer Plugins: {verwaltung.ordner}")
                return 0
            for stand in staende:
                marke = "aktiv " if stand.aktiv else "ruht  "
                vertrauen = ("signiert" if stand.signatur_gueltig else
                             "signiert, nicht pruefbar" if stand.signiert else
                             "NICHT signiert")
                print(f"{marke} {stand.manifest.id:20s} {stand.manifest.version:8s} "
                      f"{stand.manifest.kategorie:12s} {vertrauen}")
                if stand.erteilte_rechte:
                    print(f"       Rechte: {', '.join(stand.erteilte_rechte)}")
                if stand.fehler:
                    print(f"       Abgeschaltet: {stand.fehler}")
            werkzeuge = verwaltung.werkzeuge()
            if werkzeuge:
                print("\nZusaetzliche Faehigkeiten:")
                for werkzeug in werkzeuge:
                    print(f"  {werkzeug.name:24s} {werkzeug.beschreibung} "
                          f"(aus {werkzeug.plugin})")
            formate = [b for b in verwaltung.beitraege() if b.startswith("Dateiformat")]
            if formate:
                print("\nZusaetzliche Ausgabeformate: " + ", ".join(formate))
            return 0

        if args.aktion in ("pruefen", "installieren"):
            if not args.paket:
                print("Bitte den Pfad zum Paket angeben.", file=sys.stderr)
                return 2
            pruefung = verwaltung.pruefen(Path(args.paket))
            manifest = pruefung.manifest
            print(f"{manifest.name} {manifest.version} ({manifest.id})")
            print(f"  Kategorie   : {manifest.kategorie}")
            print(f"  Herausgeber : {manifest.autor or 'nicht angegeben'}")
            print(f"  Beschreibung: {manifest.beschreibung}")
            print("  Signatur    : "
                  + ("gueltig" if pruefung.signatur_gueltig else
                     "vorhanden, nicht pruefbar" if pruefung.signiert else "keine"))
            print("  Verlangte Berechtigungen:")
            if not manifest.berechtigungen:
                print("    (keine)")
            for zeile in verwaltung.rechtebeschreibung(manifest.berechtigungen):
                schwer = " [wiegt schwer]" if zeile.split(":")[0] in SCHWERWIEGEND else ""
                print(f"    {zeile}{schwer}")
            for hinweis in pruefung.hinweise:
                print(f"  Hinweis: {hinweis}")

            if args.aktion == "pruefen":
                print("\nInstalliert wurde nichts. Mit "
                      "'plugin installieren <paket> --bestaetigen' fortfahren.")
                return 0

            if not args.bestaetigen:
                print("\nAbgebrochen: die Installation braucht --bestaetigen.",
                      file=sys.stderr)
                return 1
            stand = verwaltung.installieren(Path(args.paket), bestaetigt=True)
            print(f"\nInstalliert: {stand.manifest.id} {stand.manifest.version}")
            if args.aktivieren:
                verwaltung.aktivieren(stand.manifest.id)
                print("Aktiviert. Beim naechsten Start steht die neue Faehigkeit bereit.")
            else:
                print("Noch nicht aktiv. Aktivieren mit: "
                      f"plugin aktivieren {stand.manifest.id}")
            return 0

        if args.aktion in ("aktivieren", "deaktivieren", "entfernen"):
            if not args.paket:
                print("Bitte die Plugin-Kennung angeben.", file=sys.stderr)
                return 2
            if args.aktion == "aktivieren":
                verwaltung.aktivieren(args.paket)
                print(f"{args.paket} ist aktiv.")
            elif args.aktion == "deaktivieren":
                verwaltung.deaktivieren(args.paket)
                print(f"{args.paket} ruht.")
            else:
                verwaltung.entfernen(args.paket, daten_behalten=not args.daten_loeschen)
                print(f"{args.paket} wurde entfernt."
                      + ("" if args.daten_loeschen else
                         " Die Daten des Plugins bleiben erhalten."))
            return 0

        print(f"Unbekannte Aktion: {args.aktion}", file=sys.stderr)
        return 2
    except PluginFehler as fehler:
        print(str(fehler), file=sys.stderr)
        return 1
    finally:
        controller.shutdown()


def cmd_modell(args) -> int:
    """Sprachmodell einrichten und pruefen (Erweiterung E6, Abschnitt 13/14).

    Ohne Sprachmodell recherchiert die Anwendung nur - sie formuliert keine
    Fachantwort. Das ist laut Auftrag ausdruecklich **kein** annehmbarer
    Endzustand, also gehoert der Weg zum Modell in die Anwendung selbst und
    nicht in eine Anleitung daneben.
    """
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        lage = controller.modell_lage()

        if args.aktion == "status":
            print(f"Modellverzeichnis: {lage['modellverzeichnis']}")
            if lage["modelle"]:
                for modell in lage["modelle"]:
                    print(f"  {modell['name']}  ({modell['groesse_gb']} GB)")
            else:
                print("  (keine Modelldatei)")
            print(f"Modelldienst     : {lage['dienst']}")
            print(f"Anbieter         : {lage['anbieter'].get('anbieter', '?')}")
            print(f"Bereit           : {'ja' if lage['bereit'] else 'nein'}")
            print(f"  {lage['hinweis']}")
            if lage["fehlt"]:
                print("\nEs fehlt: " + ", ".join(lage["fehlt"]))
                print("Naechster Schritt:  modell einrichten")
                return 2
            return 0

        if args.aktion == "empfehlen":
            hardware = lage["hardware"]
            print("Erkannte Hardware")
            print(f"  Arbeitsspeicher : {hardware['arbeitsspeicher_gb'] or 'unbekannt'} GB")
            print(f"  Prozessorkerne  : {hardware['kerne'] or 'unbekannt'}")
            print(f"  Grafikkarte     : {hardware['grafik'] or 'keine erkannt'}")
            print(f"  Freier Platz    : {hardware['freier_platz_gb'] or '?'} GB")
            print(f"\nEmpfohlen: {lage['empfohlenes_profil_text']}\n")

            if lage["katalogfehler"]:
                print(lage["katalogfehler"], file=sys.stderr)
                return 1
            print("Hinterlegte Bezugsquellen:")
            for eintrag in lage["katalog"]:
                marke = ">>" if (lage["empfehlung"] and
                                 eintrag["id"] == lage["empfehlung"]["id"]) else "  "
                print(f"{marke} {eintrag['id']:16s} {eintrag['name']}")
                print(f"     etwa {eintrag['groesse_gb']} GB · mindestens "
                      f"{eintrag['min_ram_gb']} GB RAM · Lizenz {eintrag['lizenz']}")
                if eintrag.get("geteilt"):
                    # Wer eine Datei erwartet und drei bekommt, haelt den
                    # Vorgang fuer kaputt. Also vorher sagen.
                    print(f"     wird in {len(eintrag['teile'])} Teildateien "
                          "geladen - alle gehoeren zusammen in models\\")
                print(f"     Bezugsquelle: {eintrag['pruefstand']}")
                if not eintrag["produktiv"]:
                    print("     NUR ZUM AUSPROBIEREN - fuer Fachfragen nicht geeignet")
                if eintrag["hinweis"]:
                    print(f"     {eintrag['hinweis']}")
            print("\nEinrichten:  modell einrichten [--profil standard] --bestaetigen")
            return 0

        if args.aktion == "einrichten":
            if lage["fehlt"] and not lage["dienst_vorhanden"]:
                print("Hinweis: Der Modelldienst (runtime/llama) fehlt in diesem "
                      "Ordner.\nEr wird mit der Windows-Fassung ausgeliefert; ohne "
                      "ihn kann ein\nheruntergeladenes Modell nicht antworten.\n",
                      file=sys.stderr)
            wunsch = args.profil or args.modell_id
            try:
                ergebnis = controller.modell_beziehen(
                    wunsch, bestaetigt=args.bestaetigen,
                    ueberschreiben=args.ueberschreiben, fortschritt=_fortschritt,
                )
            except ValueError as fehler:
                print(str(fehler), file=sys.stderr)
                if not args.bestaetigen:
                    print("\nWenn das so gewollt ist:  modell einrichten "
                          "--bestaetigen", file=sys.stderr)
                return 1
            print()
            print(ergebnis["meldung"])
            if not ergebnis["ok"]:
                return 1
            print(f"SHA-256: {ergebnis['pruefsumme']}")
            if not ergebnis["pruefsumme_vergleichbar"]:
                print("Hinweis: fuer diese Bezugsquelle liegt keine hinterlegte "
                      "Pruefsumme vor.\nDie Datei wurde daher nicht auf "
                      "Unversehrtheit geprueft.")
            print("\nModell wird eingebunden ...")
            controller.modell_neu_laden()
            return _probe_ausgeben(controller)

        if args.aktion == "laden":
            if not args.url:
                print("Es wird --url benoetigt.", file=sys.stderr)
                return 2
            if not controller.lage.online_moeglich:
                print(f"Betriebsart {controller.mode.value} - es wird nichts geladen.",
                      file=sys.stderr)
                return 2
            from pkc.llm.bezug import laden

            print(f"Lade nach {lage['modellverzeichnis']}")
            ergebnis = laden(args.url, controller.paths.get("models"), args.pruefsumme,
                             args.name, ueberschreiben=args.ueberschreiben,
                             fortschritt=_fortschritt)
            print()
            print(ergebnis.meldung)
            if not ergebnis.ok:
                return 1
            print(f"SHA-256: {ergebnis.pruefsumme}")
            controller.modell_neu_laden()
            return _probe_ausgeben(controller)

        if args.aktion == "pruefen":
            return _probe_ausgeben(controller)

        print(f"Unbekannte Aktion: {args.aktion}", file=sys.stderr)
        return 2
    finally:
        controller.shutdown()


def _fortschritt(geladen: int, gesamt: int, tempo: float) -> None:
    if gesamt:
        print(f"\r  {geladen * 100 / gesamt:5.1f} %  "
              f"{geladen / 1024**3:5.2f} von {gesamt / 1024**3:5.2f} GB  "
              f"{tempo / 1024**2:5.1f} MB/s", end="", flush=True)
    else:
        print(f"\r  {geladen / 1024**3:5.2f} GB", end="", flush=True)


def _probe_ausgeben(controller) -> int:
    """Stellt dem Modell eine Frage und sagt, was tatsaechlich passiert ist."""
    print("\nProbe: eine kleine Frage an das Modell ...")
    ergebnis = controller.modell_probe()
    if not ergebnis["ok"]:
        print(f"Das Modell hat NICHT geantwortet: {ergebnis['grund']}", file=sys.stderr)
        return 1
    print(f"\nAntwort nach {ergebnis['dauer_s']} s ({ergebnis['anbieter']}, "
          f"{ergebnis['modell']}):")
    print(f"  {ergebnis['text']}")
    if ergebnis["token_je_sekunde"]:
        print(f"\nGeschwindigkeit: etwa {ergebnis['token_je_sekunde']} Token je Sekunde")
    print("\nDas Sprachmodell ist einsatzbereit.")
    return 0


def cmd_modus(args) -> int:
    """Betriebsmodus anzeigen oder wechseln (HYBRID / OFFLINE / ONLINE).

    Die Wahl wird gespeichert und ueberlebt einen Neustart. Sie wird von der
    Anwendung nie selbsttaetig aufgehoben - ein wiederkehrendes Netz darf
    niemanden unbemerkt in den Onlinebetrieb versetzen.
    """
    controller = _controller(args)
    try:
        if args.neuer_modus:
            lage = controller.set_mode(args.neuer_modus, grund="Kommandozeile")
            print(lage.modus.beschreibung)
            print()
        lage = controller.lage
        print(f"Betriebsmodus : {lage.modus.value}   ({lage.modus.label})")
        print(f"Internet      : {lage.internet_text}")
        print(f"Onlinezugriff : {'moeglich' if lage.online_moeglich else 'nicht moeglich'}")
        if lage.grund:
            print(f"                {lage.grund}")
        return 0
    finally:
        controller.shutdown()


def cmd_quellen(args) -> int:
    """Quellenregister ansehen und Adressen berichtigen (Masterprompt 27).

    Anlass: Beim ersten echten Update schlugen fuenf Dokumente mit HTTP 404
    fehl - amtliche Stellen bauen ihre Webauftritte um, die hinterlegten
    Adressen zeigten ins Leere. Das ist ein Registerproblem, kein
    Programmfehler, und muss ohne Programmaenderung zu beheben sein. Bis
    hierher hiess das: JSON von Hand bearbeiten.
    """
    import json as _json

    controller = _controller(args)
    try:
        pfad = controller.paths.get("config") / "source_registry.json"
        register = _json.loads(pfad.read_text(encoding="utf-8"))
        quellen = register["sources"]

        if args.aktion == "liste":
            for quelle in quellen:
                zustand = "an " if quelle.get("enabled", True) else "aus"
                print(f"[{zustand}] {quelle['source_id']:26} {quelle['name']}")
                for dokument in quelle.get("documents", []):
                    print(f"        {dokument['doc_uid']:24} {dokument['url']}")
            return 0

        if args.aktion == "pruefen":
            from pkc.updater.http_client import HttpClient

            # Der Vergleich laeuft ueber die Aufzaehlung, nicht ueber eine
            # Zeichenkette: Mode.OFFLINE ist "OFFLINE" in Grossbuchstaben.
            # Ein Vergleich mit "offline" greift nie - und ausgerechnet bei
            # einer Sperre faellt das nicht auf, weil dann einfach abgerufen
            # wird, statt dass etwas scheitert.
            if controller.mode is Mode.OFFLINE:
                print("Betriebsart OFFLINE - es wird nichts abgerufen.")
                return 2
            # Abgerufen wird mit GET - genau wie beim Wissensabgleich. Eine
            # Pruefung mit HEAD misst etwas anderes: manche Server
            # beantworten HEAD gar nicht oder anders als GET. Dann meldet
            # dieser Befehl eine Quelle als kaputt, die im Betrieb laeuft
            # (oder umgekehrt) - und beides ist schlimmer als langsam.
            client = HttpClient()
            fehler = 0
            for quelle in quellen:
                if args.quelle and quelle["source_id"] not in args.quelle:
                    continue
                for dokument in quelle.get("documents", []):
                    ergebnis = client.fetch(dokument["url"])
                    zeichen = "OK  " if ergebnis.ok else "FEHL"
                    print(f"{zeichen} {dokument['doc_uid']:24} {dokument['url']}")
                    if not ergebnis.ok:
                        fehler += 1
                        print(f"       {ergebnis.error}")
            print(f"\n{fehler} Adresse(n) nicht erreichbar.")
            return 0 if fehler == 0 else 1

        if args.aktion == "setzen":
            if not args.dokument or not args.url:
                print("Es werden --dokument und --url benoetigt.", file=sys.stderr)
                return 2
            for quelle in quellen:
                for dokument in quelle.get("documents", []):
                    if dokument["doc_uid"] == args.dokument:
                        alt_url = dokument["url"]
                        dokument["url"] = args.url
                        pfad.write_text(
                            _json.dumps(register, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
                        controller.audit.record("quelle_geaendert", "source",
                                                args.dokument, alt=alt_url, neu=args.url)
                        print(f"{args.dokument}\n  vorher : {alt_url}\n  jetzt  : {args.url}")
                        print("\nDie Anwendung muss dafuer nicht neu gebaut werden.")
                        return 0
            print(f"Unbekanntes Dokument: {args.dokument}", file=sys.stderr)
            return 1

        return 2
    finally:
        controller.shutdown()


def cmd_kunde(args) -> int:
    """Kundenbereiche verwalten (Masterprompt 61, 62)."""
    controller = _controller(args)
    try:
        if args.aktion == "liste":
            bereiche = controller.customers()
            if not bereiche:
                print("Keine getrennten Kundenbereiche angelegt "
                      "(die Anwendung laeuft als Einzelinstanz).")
            for eintrag in bereiche:
                marke = "*" if eintrag["aktiv"] else " "
                groesse = eintrag["groesse_bytes"] / 1024
                print(f" {marke} {eintrag['kennung']:24s} {groesse:8.1f} KiB  "
                      f"{eintrag['verzeichnis']}")
            return 0
        if args.aktion == "anlegen":
            ergebnis = controller.create_customer(args.kennung, args.name)
            print(f"Kundenbereich angelegt: {ergebnis['kennung']}")
            print(f"  {ergebnis['verzeichnis']}")
            print("\nMit --kunde-bereich " + ergebnis["kennung"] + " arbeiten.")
            return 0
        if args.aktion == "export":
            ergebnis = controller.export_customer(args.ziel or None)
            print(f"Export: {ergebnis['verzeichnis']}")
            for datei in ergebnis["dateien"]:
                print(f"  {datei}")
            return 0
        if args.aktion == "loeschen":
            ergebnis = controller.delete_customer(
                args.kennung, confirm=args.bestaetigen,
                export_first=not args.ohne_export,
            )
            print(f"Kundenbereich geloescht: {ergebnis['kennung']} "
                  f"({ergebnis['geloeschte_dateien']} Dateien)")
            if ergebnis["export"]:
                print(f"Vorher gesichert nach: {ergebnis['export']}")
            return 0
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        controller.shutdown()


def cmd_lizenz(args) -> int:
    """Lizenzangaben ansehen, Aktivierung vorbereiten, Lizenz aufnehmen."""
    controller = _controller(args)
    try:
        status = controller.license_status
        if args.aktion == "info":
            print(status.as_text())
            return 0 if status.productive_allowed else 1
        if args.aktion == "anfrage":
            anfrage = controller.license.activation_request(args.kunde)
            text = json.dumps(anfrage, indent=2, ensure_ascii=False)
            if args.datei:
                pfad = Path(args.datei)
                pfad.write_text(text + "\n", encoding="utf-8")
                print(f"Aktivierungsanfrage geschrieben: {pfad}")
            else:
                print(text)
            print("\nDiese Angaben an den Hersteller senden. Sie enthalten keine "
                  "Unternehmensdaten.", file=sys.stderr)
            return 0
        if args.aktion == "aufnehmen":
            if not args.lizenz or not args.signatur:
                print("Es werden --lizenz und --signatur benoetigt.", file=sys.stderr)
                return 2
            neu = controller.license.install(Path(args.lizenz), Path(args.signatur))
            print(neu.as_text())
            return 0 if neu.productive_allowed else 1
        return 2
    finally:
        controller.shutdown()


def cmd_reife(args) -> int:
    """Commercial-Readiness anzeigen (Masterprompt 77, 97)."""
    from pkc.product import check_readiness

    wurzel = get_paths().program_root
    bericht = check_readiness(wurzel, run_tests=args.mit_tests)
    if args.json:
        print(json.dumps(bericht.as_dict(), indent=2, ensure_ascii=False))
    else:
        print(bericht.as_text())
    return 0 if bericht.commercial_ready else 1


def cmd_version(args) -> int:
    controller = _controller(args)
    try:
        if args.json:
            print(json.dumps(controller.versions(), indent=2, ensure_ascii=False))
        else:
            print(controller.versions_text())
        return 0
    finally:
        controller.shutdown()


def cmd_status(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        print(json.dumps(controller.status(), indent=2, ensure_ascii=False))
        return 0
    finally:
        controller.shutdown()


def cmd_onboarding(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        questions = controller.onboarding_questions()
        done = sum(1 for q in questions if q["beantwortet"])
        print(f"Unternehmens-Onboarding: {done} von {len(questions)} beantwortet\n")
        for question in questions:
            if question["beantwortet"] and not args.alle:
                continue
            if args.interaktiv:
                try:
                    value = input(f"{question['titel']}: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if value:
                    controller.answer_onboarding(question["key"], value)
            else:
                mark = "x" if question["beantwortet"] else " "
                print(f"  [{mark}] {question['titel']:34s} {question['wert'][:44]}")
        return 0
    finally:
        controller.shutdown()


def cmd_einrichten(args) -> int:
    """Zeigt den Stand der Einrichtung (Masterprompt 74)."""
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        erledigt, gesamt = controller.setup_progress()
        print(f"Einrichtung: {erledigt} von {gesamt} Schritten erledigt\n")
        for schritt in controller.setup_wizard_steps():
            marke = "x" if schritt["erledigt"] else " "
            print(f"  [{marke}] {schritt['nummer']}. {schritt['schritt']}")
            print(f"        {schritt['hinweis']}")
            if not schritt["erledigt"]:
                print(f"        -> {schritt['befehl']}")
        return 0
    finally:
        controller.shutdown()


def cmd_backup(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        info = controller.backup(args.name, args.ziel or None)
        print(f"Sicherung: {info['pfad']}"
              + ("  (ausserhalb des Datentraegers)" if info["extern"] else ""))
        for name, checksum in info["pruefsummen"].items():
            print(f"  {name:24s} {checksum[:16]}...")
        return 0
    finally:
        controller.shutdown()


def cmd_document(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.loeschen:
            print("geloescht" if controller.delete_document(args.loeschen)
                  else "nicht gefunden")
        elif args.datei:
            result = controller.add_document(args.datei)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            for item in controller.documents():
                print(f"  {item['doc_uid']}  {item['title'][:52]:52s} {item['status']}")
        return 0
    finally:
        controller.shutdown()


def cmd_approvals(args) -> int:
    controller = _controller(args)
    try:
        controller.bootstrap(build_embeddings=False)
        if args.freigeben:
            approval = controller.approvals.transition(
                args.freigeben, ApprovalState.FREIGEGEBEN, by=args.durch or "benutzer"
            )
            print(f"{approval.uid}: {approval.state.value}")
        else:
            for approval in controller.approvals.list():
                print(f"  {approval.uid}  {approval.state.value:12s} {approval.title}")
        return 0
    finally:
        controller.shutdown()


#: Die allgemeinen Schalter. Sie gelten fuer jeden Unterbefehl.
GLOBAL_OPTIONS = ("root", "offline", "quiet", "kunde_bereich")


def _global_options(parser: argparse.ArgumentParser, suppress: bool = False) -> None:
    """Die allgemeinen Schalter.

    Sie werden am Hauptbefehl *und* an jedem Unterbefehl angeboten, damit
    sowohl ``... --quiet check`` als auch ``... check --quiet`` funktioniert.
    Ein Anwender soll nicht raten muessen, wo der Schalter hingehoert.
    """
    leer = argparse.SUPPRESS if suppress else None
    parser.add_argument("--root", default=leer,
                        help="Datenverzeichnis (Standard: automatisch erkannt)")
    parser.add_argument("--offline", action="store_true", default=leer,
                        help="Netzpruefung ueberspringen")
    parser.add_argument("--quiet", action="store_true", default=leer,
                        help="weniger Ausgaben")
    parser.add_argument("--kunde-bereich", dest="kunde_bereich", default=leer,
                        help="Datenbereich eines bestimmten Unternehmens verwenden")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portabler-buchhalter",
        description="Portabler KI-Buchhalter - Kommandozeile",
    )
    _global_options(parser)
    # Dieselben Schalter noch einmal fuer die Unterbefehle. SUPPRESS sorgt
    # dafuer, dass ein nicht angegebener Schalter den Wert vom Hauptbefehl
    # nicht ueberschreibt.
    gemeinsam = argparse.ArgumentParser(add_help=False)
    _global_options(gemeinsam, suppress=True)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=argparse.ArgumentParser)

    def neu(name: str, hilfe: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, help=hilfe, parents=[gemeinsam])

    check = neu("check", "Systempruefung")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=cmd_check)

    ask = neu("frage", "Eine Fachfrage stellen")
    ask.add_argument("frage")
    ask.add_argument("--stand", help="Rechtsstand (JJJJ-MM-TT) fuer zeitbezogene Recherche")
    ask.add_argument("--merken", action="store_true",
                     help="erkannte Unternehmensinformationen ohne Rueckfrage speichern")
    ask.set_defaults(func=cmd_ask)

    chat = neu("chat", "Interaktive Unterhaltung")
    chat.set_defaults(func=cmd_chat)

    memory = neu("wissen", "Unternehmensgedaechtnis verwalten")
    memory.add_argument("action",
                        choices=["list", "get", "set", "delete", "history", "search", "export"])
    memory.add_argument("key", nargs="?", default="")
    memory.add_argument("wert", nargs="?", default="")
    memory.add_argument("--titel", default="")
    memory.add_argument("--kategorie", default="")
    memory.add_argument("--status", default="active")
    memory.add_argument("--endgueltig", action="store_true")
    memory.set_defaults(func=cmd_memory)

    update = neu("update", "Wissensupdate")
    update.add_argument("--quelle", action="append", help="nur diese Quelle(n)")
    update.add_argument("--trocken", action="store_true", help="Trockenlauf ohne Schreiben")
    update.add_argument("--zuruecknehmen", help="Lauf-ID zuruecknehmen")
    update.set_defaults(func=cmd_update)

    status = neu("status", "Lagebericht als JSON")
    status.set_defaults(func=cmd_status)

    lizenz = neu("lizenz", "Lizenz ansehen, anfragen oder aufnehmen")
    lizenz.add_argument("aktion", nargs="?", default="info",
                        choices=["info", "anfrage", "aufnehmen"])
    lizenz.add_argument("--kunde", default="", help="Firmenname fuer die Anfrage")
    lizenz.add_argument("--datei", default="", help="Anfrage in diese Datei schreiben")
    lizenz.add_argument("--lizenz", default="", help="Pfad zu license.json")
    lizenz.add_argument("--signatur", default="", help="Pfad zu license.sig")
    lizenz.set_defaults(func=cmd_lizenz)

    recherche = neu("recherche", "Rohe Fundstellen zu einer Frage anzeigen")
    recherche.add_argument("frage")
    recherche.set_defaults(func=cmd_recherche)

    modell = neu("modell", "Sprachmodell einrichten und pruefen")
    modell.add_argument("aktion", nargs="?", default="status",
                        choices=["status", "empfehlen", "einrichten", "laden", "pruefen"])
    modell.add_argument("--profil", default="",
                        help="probe, light, standard oder high")
    modell.add_argument("--modell-id", dest="modell_id", default="",
                        help="Kennung aus dem Katalog, z.B. qwen2.5-7b")
    modell.add_argument("--bestaetigen", action="store_true",
                        help="den Bezug ausdruecklich bestaetigen")
    modell.add_argument("--ueberschreiben", action="store_true")
    modell.add_argument("--url", default="", help="Bezugsadresse der Modelldatei")
    modell.add_argument("--pruefsumme", default="", help="erwartete SHA-256")
    modell.add_argument("--name", default="", help="Dateiname im Modellordner")
    modell.set_defaults(func=cmd_modell)

    datei = neu("datei", "Ergebnisse als Datei ausgeben (Excel, Word, PDF ...)")
    datei.add_argument("aktion", nargs="?", default="antwort",
                       choices=["antwort", "text", "formate", "liste"])
    datei.add_argument("--format", default="pdf",
                       help="txt, md, json, csv, xlsx, docx, pptx oder pdf")
    datei.add_argument("--name", default="", help="Dateiname ohne Endung")
    datei.add_argument("--text", default="", help="Inhalt fuer die Aktion 'text'")
    datei.add_argument("--ueberschreiben", action="store_true",
                       help="vorhandene Datei ersetzen statt neue Fassung anlegen")
    datei.set_defaults(func=cmd_datei)

    plugin = neu("plugin", "Plugins ansehen, installieren, aktivieren")
    plugin.add_argument("aktion", nargs="?", default="liste",
                        choices=["liste", "pruefen", "installieren", "aktivieren",
                                 "deaktivieren", "entfernen"])
    plugin.add_argument("paket", nargs="?", default="",
                        help="Pfad zum Paket (.kimplug) bzw. Kennung")
    plugin.add_argument("--bestaetigen", action="store_true",
                        help="die verlangten Berechtigungen erteilen")
    plugin.add_argument("--aktivieren", action="store_true",
                        help="nach dem Installieren gleich aktivieren")
    plugin.add_argument("--daten-loeschen", dest="daten_loeschen", action="store_true",
                        help="beim Entfernen auch die Daten des Plugins loeschen")
    plugin.set_defaults(func=cmd_plugin)

    modus = neu("modus", "Betriebsmodus anzeigen oder wechseln")
    modus.add_argument("neuer_modus", nargs="?", default="",
                       choices=["", "HYBRID", "OFFLINE", "ONLINE",
                                "hybrid", "offline", "online"],
                       help="ohne Angabe wird nur der aktuelle Stand gezeigt")
    modus.set_defaults(func=cmd_modus)

    quellen = neu("quellen", "Quellenregister ansehen und Adressen berichtigen")
    quellen.add_argument("aktion", nargs="?", default="liste",
                         choices=["liste", "pruefen", "setzen"])
    quellen.add_argument("--quelle", action="append", default=[],
                         help="nur diese Quellen-ID pruefen (mehrfach moeglich)")
    quellen.add_argument("--dokument", default="", help="doc_uid des zu aendernden Dokuments")
    quellen.add_argument("--url", default="", help="neue Adresse")
    quellen.set_defaults(func=cmd_quellen)

    kunde = neu("kunde", "Kundenbereiche verwalten")
    kunde.add_argument("aktion", choices=["liste", "anlegen", "export", "loeschen"])
    kunde.add_argument("kennung", nargs="?", default="")
    kunde.add_argument("--name", default="")
    kunde.add_argument("--ziel", default="")
    kunde.add_argument("--bestaetigen", default="",
                       help="zum Loeschen die Kundenkennung wiederholen")
    kunde.add_argument("--ohne-export", dest="ohne_export", action="store_true")
    kunde.set_defaults(func=cmd_kunde)

    reife = neu("reife", "Stand auf dem Weg zur kommerziellen Freigabe")
    reife.add_argument("--mit-tests", dest="mit_tests", action="store_true")
    reife.add_argument("--json", action="store_true")
    reife.set_defaults(func=cmd_reife)

    version = neu("version", "Produkt-, Modul- und Wissensversionen")
    version.add_argument("--json", action="store_true")
    version.set_defaults(func=cmd_version)

    onboarding = neu("onboarding", "Unternehmensdaten erfassen")
    onboarding.add_argument("--interaktiv", action="store_true")
    onboarding.add_argument("--alle", action="store_true")
    onboarding.set_defaults(func=cmd_onboarding)

    backup = neu("sicherung", "Sicherung erstellen")
    backup.add_argument("--name", default="")
    backup.add_argument("--ziel", default="",
                        help="zweites Sicherungsziel, z.B. eine andere SSD oder ein NAS")
    backup.set_defaults(func=cmd_backup)

    einrichten = neu("einrichten", "Gefuehrte Einrichtung: was fehlt noch?")
    einrichten.set_defaults(func=cmd_einrichten)

    document = neu("beleg", "Beleg hinzufuegen oder auflisten")
    document.add_argument("datei", nargs="?")
    document.add_argument("--loeschen", default="", help="Beleg-Kennung loeschen")
    document.set_defaults(func=cmd_document)

    approvals = neu("freigaben", "Freigaben anzeigen oder erteilen")
    approvals.add_argument("--freigeben", help="Kennung des Vorgangs")
    approvals.add_argument("--durch", help="Name der freigebenden Person")
    approvals.set_defaults(func=cmd_approvals)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
