"""Kommandozeile: die Schalter muessen dort funktionieren, wo man sie erwartet."""

from __future__ import annotations

import pytest

from ui.cli import GLOBAL_OPTIONS, build_parser


@pytest.mark.parametrize("argumente", [
    ["--quiet", "check"],
    ["check", "--quiet"],
    ["--offline", "--quiet", "check"],
    ["check", "--offline", "--quiet"],
])
def test_global_options_work_in_both_positions(argumente):
    """``check --quiet`` und ``--quiet check`` muessen beide gehen.

    Diese Luecke fiel im Windows-Ablauf auf: der Rauchtest der gebauten EXE
    schlug mit "unrecognized arguments: --quiet" fehl, weil der Schalter nur
    vor dem Unterbefehl erlaubt war.
    """
    args = build_parser().parse_args(argumente)
    assert args.command == "check"
    assert args.quiet is True


def test_option_before_subcommand_is_not_overwritten():
    """Ein vorne gesetzter Schalter darf hinten nicht auf den Standard zurueckfallen."""
    args = build_parser().parse_args(["--quiet", "--offline", "frage", "Testfrage"])
    assert args.quiet is True and args.offline is True
    assert args.frage == "Testfrage"


def test_root_option_in_both_positions(tmp_path):
    vorne = build_parser().parse_args(["--root", str(tmp_path), "status"])
    hinten = build_parser().parse_args(["status", "--root", str(tmp_path)])
    assert vorne.root == hinten.root == str(tmp_path)


def test_all_subcommands_accept_the_global_options():
    parser = build_parser()
    befehle = {
        "check": [], "frage": ["x"], "chat": [], "wissen": ["list"], "update": [],
        "status": [], "onboarding": [], "sicherung": [], "beleg": [], "freigaben": [],
    }
    for befehl, zusatz in befehle.items():
        args = parser.parse_args([befehl, *zusatz, "--quiet"])
        assert args.quiet is True, f"{befehl} nimmt --quiet nicht an"


@pytest.mark.parametrize("schalter,ziel,wert", [
    (["--kunde-bereich", "kunde_a"], "kunde_bereich", "kunde_a"),
    (["--root", "/tmp/x"], "root", "/tmp/x"),
])
@pytest.mark.parametrize("position", ["vorne", "hinten"])
def test_kundenbereich_und_root_in_beiden_positionen(schalter, ziel, wert, position):
    """Jeder allgemeine Schalter muss vor und nach dem Unterbefehl gehen.

    Hintergrund: --kunde-bereich fehlte am Hauptbefehl vollstaendig. Der
    Aufruf brach mit "invalid choice" ab - aufgefallen erst im Durchlauf mit
    der echten Anwendung, nicht in den Tests.
    """
    argumente = (schalter + ["status"]) if position == "vorne" else (["status"] + schalter)
    args = build_parser().parse_args(argumente)
    assert args.command == "status"
    assert getattr(args, ziel) == wert


def test_alle_allgemeinen_schalter_sind_ueberall_vorhanden():
    """Kein allgemeiner Schalter darf an einem Unterbefehl fehlen."""
    parser = build_parser()
    befehle = {
        "check": [], "frage": ["x"], "chat": [], "wissen": ["list"], "update": [],
        "status": [], "onboarding": [], "sicherung": [], "beleg": [],
        "freigaben": [], "lizenz": [], "version": [], "reife": [],
        "einrichten": [], "kunde": ["liste"],
    }
    for befehl, zusatz in befehle.items():
        args = parser.parse_args([befehl, *zusatz])
        for schalter in GLOBAL_OPTIONS:
            assert hasattr(args, schalter), f"{befehl} kennt --{schalter} nicht"
        # und am Hauptbefehl davor
        davor = parser.parse_args(["--kunde-bereich", "k1", befehl, *zusatz])
        assert davor.kunde_bereich == "k1", f"{befehl}: Schalter vorne wirkt nicht"


# ======================================================================
# Quellenregister ueber die Kommandozeile pflegen
#
# Anlass: Beim ersten echten Wissensupdate schlugen fuenf Dokumente mit
# HTTP 404 fehl, weil amtliche Stellen ihre Webauftritte umgebaut hatten.
# Das ist ohne Programmaenderung zu beheben - aber bis hierher nur, indem
# man JSON von Hand bearbeitet.
# ======================================================================

def test_quellen_liste_zeigt_alle_adressen(portable_root, capsys):
    from ui.cli import main

    assert main(["--root", str(portable_root.root), "--offline", "quellen", "liste"]) == 0
    ausgabe = capsys.readouterr().out
    assert "Q01_GESETZE_IM_INTERNET" in ausgabe
    assert "https://" in ausgabe


def test_quellen_setzen_berichtigt_eine_adresse(portable_root, capsys):
    import json
    from ui.cli import main

    wurzel = str(portable_root.root)
    assert main([wurzel and "--root", wurzel, "--offline", "quellen", "liste"]) == 0
    capsys.readouterr()

    code = main(["--root", wurzel, "--offline", "quellen", "setzen",
                 "--dokument", "GII_USTG", "--url", "https://beispiel.invalid/neu"])
    assert code == 0
    assert "https://beispiel.invalid/neu" in capsys.readouterr().out

    register = json.loads(
        (portable_root.get("config") / "source_registry.json").read_text(encoding="utf-8"))
    adressen = [d["url"] for q in register["sources"] for d in q.get("documents", [])]
    assert "https://beispiel.invalid/neu" in adressen


def test_quellen_setzen_meldet_unbekanntes_dokument(portable_root, capsys):
    from ui.cli import main

    code = main(["--root", str(portable_root.root), "--offline", "quellen", "setzen",
                 "--dokument", "GIBT_ES_NICHT", "--url", "https://beispiel.invalid/x"])
    assert code == 1
    assert "Unbekanntes Dokument" in capsys.readouterr().err


def test_quellen_pruefen_ruft_offline_nichts_ab(portable_root, capsys, monkeypatch):
    """Die Offlinezusage gilt auch hier - und zwar wirklich.

    Der erste Entwurf verglich die Betriebsart mit der Zeichenkette
    "offline". Mode.OFFLINE ist aber "OFFLINE" in Grossbuchstaben; der
    Vergleich griff nie, und der Befehl rief munter ab. Ausgerechnet bei
    einer Sperre faellt so ein Fehler nicht auf, weil das Programm dann
    einfach das Falsche tut, statt zu scheitern.
    """
    from ui.cli import main

    def darf_nicht(*args, **kwargs):
        raise AssertionError("Im OFFLINE-Betrieb darf nichts abgerufen werden.")

    monkeypatch.setattr("pkc.updater.http_client.HttpClient.fetch", darf_nicht)

    code = main(["--root", str(portable_root.root), "--offline", "quellen", "pruefen"])
    assert code == 2
    assert "OFFLINE" in capsys.readouterr().out


def test_quellen_pruefen_fragt_wie_der_abgleich(portable_root, capsys, monkeypatch):
    """Geprueft werden muss das, was im Betrieb passiert.

    Der Befehl fragte mit HEAD, der Wissensabgleich fragt mit GET. Manche
    Server beantworten HEAD gar nicht - dann meldet der Befehl eine Quelle
    als kaputt, die laeuft, und jemand bessert eine Adresse aus, die nie
    falsch war. Der umgekehrte Fall ist noch unangenehmer.
    """
    from pkc.updater.http_client import FetchResult
    from ui.cli import main

    verfahren = []

    def merken(self, url, etag=None, last_modified=None, method="GET"):
        verfahren.append(method)
        return FetchResult(url, 200, True, content=b"x")

    monkeypatch.setattr("pkc.updater.http_client.HttpClient.fetch", merken)

    code = main(["--root", str(portable_root.root), "quellen", "pruefen",
                 "--quelle", "Q01_GESETZE_IM_INTERNET"])
    capsys.readouterr()
    assert code == 0
    assert verfahren, "es wurde gar nichts abgerufen"
    assert set(verfahren) == {"GET"}, (
        f"abgerufen wurde mit {sorted(set(verfahren))} - der Abgleich nimmt GET")


# ======================================================================
# Die Unterbefehle mit einer Kennung
#
# Anlass: eine Umbenennung im Plugin-Befehl hat versehentlich auch den
# Kundenbefehl getroffen - `kunde anlegen` griff danach auf ein Feld zu,
# das es dort gar nicht gibt. Alle Tests blieben gruen, weil kein Test
# diesen Weg lief. Der Fehler faellt erst auf, wenn man den Befehl
# tatsaechlich ausfuehrt. Also wird er jetzt ausgefuehrt.
# ======================================================================

def test_kunde_anlegen_liste_und_loeschen(portable_root, capsys):
    from ui.cli import main

    wurzel = str(portable_root.root)
    assert main(["--root", wurzel, "--offline", "kunde", "anlegen", "musterfirma",
                 "--name", "Muster GmbH"]) == 0
    assert "musterfirma" in capsys.readouterr().out

    assert main(["--root", wurzel, "--offline", "kunde", "liste"]) == 0
    assert "musterfirma" in capsys.readouterr().out

    # Der gerade geoeffnete Bereich laesst sich bewusst nicht loeschen -
    # deshalb hier ohne --kunde-bereich.
    assert main(["--root", wurzel, "--offline", "kunde", "loeschen", "musterfirma",
                 "--bestaetigen", "musterfirma"]) == 0
    ausgabe = capsys.readouterr().out
    assert "geloescht" in ausgabe.lower()


def test_plugin_liste_laeuft_ohne_installiertes_plugin(portable_root, capsys):
    from ui.cli import main

    assert main(["--root", str(portable_root.root), "--offline", "plugin", "liste"]) == 0
    assert "kein Plugin installiert" in capsys.readouterr().out


def test_datei_formate_nennt_die_acht_formate(portable_root, capsys):
    from ui.cli import main

    assert main(["--root", str(portable_root.root), "--offline", "datei", "formate"]) == 0
    ausgabe = capsys.readouterr().out
    for format in ("xlsx", "docx", "pptx", "pdf", "csv", "txt", "md", "json"):
        assert format in ausgabe


def test_datei_ohne_antwort_meldet_das_verstaendlich(portable_root, capsys):
    from ui.cli import main

    code = main(["--root", str(portable_root.root), "--offline", "datei", "antwort"])
    assert code == 1
    assert "noch keine Antwort" in capsys.readouterr().err
