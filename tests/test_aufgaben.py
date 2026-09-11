"""Geplante Aufgaben - Ausloeser, Ausfuehrung, Windows-Eintrag.

Der Bereich "Aufgaben & Automationen" war der zweite, hinter dem nur
eine leere Tuer stand. Niels hat sich fuer Weg C entschieden: Aufgaben
laufen, solange PORTIVA offen ist; wer mehr will, schaltet die
Windows-Aufgabenplanung ausdruecklich dazu.

Die Tests kreisen um drei Zusicherungen:

1. Eine Aufgabe, die nicht laufen konnte, gilt **nicht** als erledigt.
2. Verpasstes wird **einmal** nachgeholt, nicht fuenfmal.
3. Eine Aktion mit Aussenwirkung braucht bei **jeder** Ausfuehrung eine
   Bestaetigung.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pkc.aufgaben import (
    Aktion, Aufgabenspeicher, Ausloeser, AusloeserFehler, AufgabenFehler,
    Planer, SPUREN, WindowsPlanung, abmelden, alle, hole, registrieren,
)

MO = datetime(2026, 9, 7, 9, 0)      # ein Montag
SA = datetime(2026, 9, 12, 9, 0)     # ein Samstag


# -- Ausloeser -----------------------------------------------------------

def test_ein_intervall_unter_einer_stunde_wird_abgelehnt():
    """Kuerzere Abstaende bringen nichts und kosten Strom."""
    with pytest.raises(AusloeserFehler) as fehler:
        Ausloeser("intervall", stunden=0)
    assert "Stunde" in str(fehler.value)


def test_eine_falsche_uhrzeit_wird_mit_beispiel_abgelehnt():
    with pytest.raises(AusloeserFehler) as fehler:
        Ausloeser("taeglich", uhrzeit="25:00")
    assert "07:30" in str(fehler.value), "der Satz muss zeigen, was geht"


def test_die_beschreibung_ist_ein_satz_und_keine_cron_zeile():
    assert Ausloeser("intervall", stunden=1).beschreibung() == "Jede Stunde"
    assert Ausloeser("intervall", stunden=24).beschreibung() == "Einmal am Tag"
    assert Ausloeser("intervall", stunden=48).beschreibung() == "Alle 2 Tage"
    assert Ausloeser("intervall", stunden=6).beschreibung() == "Alle 6 Stunden"
    assert Ausloeser("beim_start").beschreibung() == "Bei jedem Programmstart"
    assert Ausloeser("manuell").beschreibung() == "Nur von Hand"
    wochentags = Ausloeser("taeglich", uhrzeit="07:30",
                           wochentage=(0, 1, 2, 3, 4))
    assert wochentags.beschreibung().startswith("Montag, Dienstag")


def test_eine_taegliche_aufgabe_ist_nach_ihrer_uhrzeit_faellig():
    ausloeser = Ausloeser("taeglich", uhrzeit="07:30")
    assert ausloeser.faellig(None, MO) is True
    gelaufen = MO.replace(hour=7, minute=31)
    assert ausloeser.faellig(gelaufen, MO) is False


def test_verpasstes_wird_einmal_nachgeholt_und_nicht_fuenfmal():
    """Fuenf Sicherungen hintereinander sind eine Sicherung und vier
    Wartezeiten."""
    ausloeser = Ausloeser("taeglich", uhrzeit="07:30")
    vor_fuenf_tagen = MO - timedelta(days=5)

    assert ausloeser.faellig(vor_fuenf_tagen, MO) is True
    # Nach dem einen Nachholen ist Ruhe - bis morgen.
    gerade_gelaufen = MO
    assert ausloeser.faellig(gerade_gelaufen, MO) is False
    morgen = MO + timedelta(days=1)
    assert ausloeser.faellig(gerade_gelaufen, morgen) is True


def test_eine_wochentagsaufgabe_ueberspringt_das_wochenende():
    werktags = Ausloeser("taeglich", uhrzeit="07:30",
                         wochentage=(0, 1, 2, 3, 4))
    # Samstag 9 Uhr: der letzte faellige Termin war Freitag.
    assert werktags.naechste(None, SA) == datetime(2026, 9, 14, 7, 30)
    freitag_gelaufen = datetime(2026, 9, 11, 7, 30)
    assert werktags.faellig(freitag_gelaufen, SA) is False


def test_eine_startaufgabe_laeuft_nur_beim_start():
    ausloeser = Ausloeser("beim_start")
    assert ausloeser.faellig(None, MO, start=True) is True
    assert ausloeser.faellig(None, MO, start=False) is False


def test_eine_aufgabe_von_hand_laeuft_nie_von_selbst():
    ausloeser = Ausloeser("manuell")
    assert ausloeser.faellig(None, MO, start=True) is False
    assert ausloeser.naechste(None, MO) is None


def test_ein_ausloeser_uebersteht_das_speichern():
    urspruenglich = Ausloeser("taeglich", uhrzeit="07:30", wochentage=(0, 4))
    wieder = Ausloeser.aus_dict(urspruenglich.as_dict())
    assert wieder == urspruenglich


# -- Speicher ------------------------------------------------------------

@pytest.fixture
def speicher(portable_root):
    return Aufgabenspeicher(portable_root)


def test_eine_aufgabe_wird_angelegt_und_wiedergefunden(speicher):
    aufgabe = speicher.anlegen("Naechtliche Sicherung", "sicherung_anlegen",
                               Ausloeser("taeglich", uhrzeit="23:00"))
    wieder = speicher.holen(aufgabe.kennung)
    assert wieder is not None
    assert wieder.name == "Naechtliche Sicherung"
    assert wieder.ausloeser.uhrzeit == "23:00"


def test_aufgaben_liegen_im_kundenbereich(portable_root, speicher):
    speicher.anlegen("Sicherung", "sicherung_anlegen", Ausloeser("manuell"))
    assert "workspace" in portable_root.get("aufgaben").parts


def test_eine_aufgabe_ohne_namen_wird_abgelehnt(speicher):
    with pytest.raises(AufgabenFehler):
        speicher.anlegen("  ", "sicherung_anlegen", Ausloeser("manuell"))


def test_pausieren_und_wieder_aktivieren(speicher):
    aufgabe = speicher.anlegen("Sicherung", "sicherung_anlegen",
                               Ausloeser("taeglich", uhrzeit="23:00"))
    speicher.umschalten(aufgabe.kennung, False)
    assert speicher.holen(aufgabe.kennung).aktiv is False
    speicher.umschalten(aufgabe.kennung, True)
    assert speicher.holen(aufgabe.kennung).aktiv is True


def test_eine_pausierte_aufgabe_ist_nie_faellig(speicher):
    aufgabe = speicher.anlegen("Sicherung", "sicherung_anlegen",
                               Ausloeser("taeglich", uhrzeit="07:30"))
    speicher.umschalten(aufgabe.kennung, False)
    assert speicher.holen(aufgabe.kennung).faellig(MO) is False


def test_eine_beschaedigte_liste_macht_den_bereich_nicht_unbenutzbar(
        speicher, portable_root):
    speicher.anlegen("Sicherung", "sicherung_anlegen", Ausloeser("manuell"))
    (portable_root.get("aufgaben") / "aufgaben.json").write_text(
        "{kaputt", encoding="utf-8")
    assert speicher.liste() == []
    assert speicher.anlegen("Neu", "sicherung_anlegen",
                            Ausloeser("manuell")) is not None


def test_das_protokoll_waechst_nicht_unbegrenzt(speicher):
    from pkc.aufgaben.modell import LAEUFE_BEHALTEN, Lauf

    aufgabe = speicher.anlegen("Sicherung", "sicherung_anlegen",
                               Ausloeser("manuell"))
    for nummer in range(LAEUFE_BEHALTEN + 10):
        aufgabe.vermerken(Lauf(zeitpunkt=str(nummer), ergebnis="ok"))
    assert len(aufgabe.protokoll) == LAEUFE_BEHALTEN
    assert aufgabe.protokoll[-1].zeitpunkt == str(LAEUFE_BEHALTEN + 9), \
        "die neuesten Laeufe muessen bleiben, nicht die aeltesten"


# -- Planer --------------------------------------------------------------

class Lage:
    def __init__(self, online: bool):
        self.online_moeglich = online


class Steuerung:
    """Ein Doppel des Controllers - nur was der Planer anfasst."""

    def __init__(self, online: bool = True):
        self.lage = Lage(online)
        self.aufrufe: list[str] = []


@pytest.fixture
def eigene_aktion():
    """Eine harmlose Aktion, die nur mitschreibt, dass sie lief."""
    def arbeiten(controller) -> str:
        controller.aufrufe.append("gelaufen")
        return "Habe etwas getan."

    aktion = registrieren(Aktion(
        kennung="pruef_aktion", name="Pruefaktion",
        beschreibung="Nur fuer Tests.", funktion=arbeiten))
    yield aktion
    abmelden("pruef_aktion")


@pytest.fixture
def netzaktion():
    def arbeiten(controller) -> str:
        controller.aufrufe.append("netz")
        return "Geholt."

    registrieren(Aktion(
        kennung="pruef_netz", name="Pruefaktion mit Netz",
        beschreibung="Nur fuer Tests.", funktion=arbeiten,
        braucht_netz=True))
    yield
    abmelden("pruef_netz")


@pytest.fixture
def aussenaktion():
    def arbeiten(controller) -> str:
        controller.aufrufe.append("aussen")
        return "Verschickt."

    registrieren(Aktion(
        kennung="pruef_aussen", name="Pruefaktion nach aussen",
        beschreibung="Nur fuer Tests.", funktion=arbeiten,
        nach_aussen=True))
    yield
    abmelden("pruef_aussen")


def test_eine_faellige_aufgabe_laeuft(speicher, eigene_aktion):
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    aufgabe = speicher.anlegen("Pruefung", "pruef_aktion",
                               Ausloeser("taeglich", uhrzeit="07:30"))

    laeufe = planer.durchlauf(jetzt=MO)
    assert [l.ergebnis for l in laeufe] == ["ok"]
    assert steuerung.aufrufe == ["gelaufen"]
    assert speicher.holen(aufgabe.kennung).letzter_lauf.startswith("2026-09-07")


def test_zweimal_hintereinander_laeuft_sie_nur_einmal(speicher, eigene_aktion):
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Pruefung", "pruef_aktion",
                     Ausloeser("taeglich", uhrzeit="07:30"))
    planer.durchlauf(jetzt=MO)
    planer.durchlauf(jetzt=MO + timedelta(minutes=1))
    assert steuerung.aufrufe == ["gelaufen"]


def test_ohne_internet_bleibt_die_aufgabe_faellig(speicher, netzaktion):
    """Der Kernsatz: was nicht laufen konnte, gilt nicht als erledigt."""
    steuerung = Steuerung(online=False)
    planer = Planer(speicher, steuerung)
    aufgabe = speicher.anlegen("Wissen", "pruef_netz",
                               Ausloeser("taeglich", uhrzeit="07:30"))

    laeufe = planer.durchlauf(jetzt=MO)
    assert [l.ergebnis for l in laeufe] == ["uebersprungen"]
    assert "Internetverbindung" in laeufe[0].meldung
    assert steuerung.aufrufe == []
    assert speicher.holen(aufgabe.kennung).letzter_lauf == "", \
        "ein uebersprungener Lauf darf die Faelligkeit nicht verschieben"
    assert speicher.holen(aufgabe.kennung).faellig(MO) is True


def test_sobald_wieder_internet_da_ist_laeuft_sie(speicher, netzaktion):
    """Gegenprobe zum vorigen Test."""
    steuerung = Steuerung(online=False)
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Wissen", "pruef_netz",
                     Ausloeser("taeglich", uhrzeit="07:30"))
    planer.durchlauf(jetzt=MO)
    steuerung.lage.online_moeglich = True
    laeufe = planer.durchlauf(jetzt=MO + timedelta(minutes=5))
    assert [l.ergebnis for l in laeufe] == ["ok"]
    assert steuerung.aufrufe == ["netz"]


def test_eine_aktion_nach_aussen_laeuft_ohne_bestaetigung_nicht(
        speicher, aussenaktion):
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Versand", "pruef_aussen",
                     Ausloeser("taeglich", uhrzeit="07:30"))

    laeufe = planer.durchlauf(jetzt=MO)
    assert laeufe[0].ergebnis == "uebersprungen"
    assert "Bestaetigung" in laeufe[0].meldung
    assert steuerung.aufrufe == []


def test_schweigen_ist_keine_zustimmung(speicher, aussenaktion):
    """Ohne Rueckfragefunktion gilt das als nicht bestaetigt."""
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Versand", "pruef_aussen",
                     Ausloeser("taeglich", uhrzeit="07:30"))
    laeufe = planer.durchlauf(jetzt=MO, bestaetigen=None)
    assert laeufe[0].ergebnis == "uebersprungen"


def test_mit_bestaetigung_laeuft_sie(speicher, aussenaktion):
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Versand", "pruef_aussen",
                     Ausloeser("taeglich", uhrzeit="07:30"))
    laeufe = planer.durchlauf(jetzt=MO, bestaetigen=lambda _a: True)
    assert laeufe[0].ergebnis == "ok"
    assert steuerung.aufrufe == ["aussen"]


def test_und_beim_naechsten_mal_wird_wieder_gefragt(speicher, aussenaktion):
    """Die Erlaubnis beim Anlegen genuegt nicht - und die von gestern auch
    nicht."""
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Versand", "pruef_aussen",
                     Ausloeser("taeglich", uhrzeit="07:30"))
    planer.durchlauf(jetzt=MO, bestaetigen=lambda _a: True)
    laeufe = planer.durchlauf(jetzt=MO + timedelta(days=1))
    assert laeufe[0].ergebnis == "uebersprungen"
    assert steuerung.aufrufe == ["aussen"], "nur der erste Lauf zaehlt"


def test_eine_fehlerhafte_aktion_stuerzt_nicht_ab(speicher):
    def scheitern(controller) -> str:
        raise RuntimeError("Der Server antwortet nicht.")

    registrieren(Aktion(kennung="pruef_fehler", name="Fehleraktion",
                        beschreibung="Nur fuer Tests.", funktion=scheitern))
    try:
        steuerung = Steuerung()
        planer = Planer(speicher, steuerung)
        aufgabe = speicher.anlegen("Fehler", "pruef_fehler",
                                   Ausloeser("taeglich", uhrzeit="07:30"))
        laeufe = planer.durchlauf(jetzt=MO)
        assert laeufe[0].ergebnis == "fehler"
        assert "Server" in laeufe[0].meldung
        assert speicher.holen(aufgabe.kennung).letzter_lauf, \
            "auch ein Fehlversuch verschiebt die Faelligkeit - sonst liefe " \
            "eine dauerhaft scheiternde Aufgabe im Minutentakt weiter"
    finally:
        abmelden("pruef_fehler")


def test_eine_verschwundene_aktion_wird_erklaert(speicher):
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Weg", "aus_einem_plugin", Ausloeser("manuell"))
    aufgabe = speicher.liste()[0]
    lauf = planer.ausfuehren(aufgabe.kennung, jetzt=MO, von_hand=True)
    assert lauf.ergebnis == "uebersprungen"
    assert "Plugin" in lauf.meldung


def test_von_hand_laeuft_auch_eine_pausierte_aufgabe(speicher, eigene_aktion):
    """Ein Knopf "Jetzt ausfuehren" muss ausfuehren."""
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    aufgabe = speicher.anlegen("Pruefung", "pruef_aktion",
                               Ausloeser("taeglich", uhrzeit="07:30"))
    speicher.umschalten(aufgabe.kennung, False)

    uebersprungen = planer.ausfuehren(aufgabe.kennung, jetzt=MO)
    assert uebersprungen.ergebnis == "uebersprungen"

    gelaufen = planer.ausfuehren(aufgabe.kennung, jetzt=MO, von_hand=True)
    assert gelaufen.ergebnis == "ok"
    assert steuerung.aufrufe == ["gelaufen"]


def test_eine_startaufgabe_laeuft_nur_im_startdurchlauf(speicher, eigene_aktion):
    steuerung = Steuerung()
    planer = Planer(speicher, steuerung)
    speicher.anlegen("Beim Start", "pruef_aktion", Ausloeser("beim_start"))

    assert planer.durchlauf(jetzt=MO) == []
    laeufe = planer.durchlauf(jetzt=MO, start=True)
    assert [l.ergebnis for l in laeufe] == ["ok"]


# -- Die mitgelieferten Aktionen ----------------------------------------

def test_es_gibt_mitgelieferte_aktionen():
    kennungen = {a.kennung for a in alle()}
    assert {"wissen_aktualisieren", "sicherung_anlegen",
            "wissensstand_pruefen"} <= kennungen


def test_jede_aktion_sagt_in_einem_satz_was_sie_tut():
    for aktion in alle():
        assert len(aktion.beschreibung) > 30, \
            f"{aktion.kennung} erklaert sich nicht"
        assert aktion.name, f"{aktion.kennung} hat keinen Namen"


def test_keine_mitgelieferte_aktion_gibt_etwas_nach_aussen():
    """Wenn sich das aendert, muss es jemandem auffallen."""
    heikel = [a.kennung for a in alle() if a.nach_aussen]
    assert not heikel, (
        "Diese Aktionen geben Daten nach aussen: " + ", ".join(heikel) +
        ". Das ist nicht verboten, aber es muss in der Anleitung stehen "
        "und in der Oberflaeche gekennzeichnet sein.")


def test_das_wissensupdate_ist_als_netzaktion_gekennzeichnet():
    assert hole("wissen_aktualisieren").braucht_netz is True
    assert hole("sicherung_anlegen").braucht_netz is False


# -- Windows-Aufgabenplanung --------------------------------------------

class Schtasks:
    """Ein Doppel fuer schtasks - kein Testrechner bekommt Eintraege."""

    def __init__(self):
        self.eintrag: dict | None = None
        self.befehle: list[list[str]] = []

    def __call__(self, befehl):
        from pkc.aufgaben.windows_planung import _Ergebnis

        self.befehle.append(befehl)
        if "/Create" in befehl:
            uhrzeit = befehl[befehl.index("/ST") + 1]
            ziel = befehl[befehl.index("/TR") + 1]
            self.eintrag = {"uhrzeit": uhrzeit, "ziel": ziel}
            return _Ergebnis(True, "ERFOLGREICH")
        if "/Delete" in befehl:
            self.eintrag = None
            return _Ergebnis(True, "ERFOLGREICH")
        if "/Query" in befehl:
            if self.eintrag is None:
                return _Ergebnis(False, "Der angegebene Task ist nicht vorhanden.")
            return _Ergebnis(True,
                             f"TaskName: PORTIVA\n"
                             f"Task To Run: {self.eintrag['ziel']}\n"
                             f"Start Time: {self.eintrag['uhrzeit']}:00\n")
        return _Ergebnis(False, "unbekannt")


@pytest.fixture
def programm(tmp_path):
    datei = tmp_path / "PORTABLE_BUCHHALTER_KONSOLE.exe"
    datei.write_bytes(b"MZ")
    return datei


def test_ohne_windows_wird_das_klar_gesagt(programm):
    planung = WindowsPlanung(programm, laufen=Schtasks(), windows=False)
    zustand = planung.zustand()
    assert zustand.moeglich is False
    assert "nur unter Windows" in zustand.hinweis
    assert "geoeffnet" in zustand.hinweis, \
        "der Satz muss sagen, was stattdessen gilt"


def test_der_hinweistext_nennt_was_zurueckbleibt():
    """Er ist das, was der Mensch vor der Zustimmung liest."""
    assert "Aufgabenplanung von Windows" in SPUREN
    assert "Laufwerksbuchstaben" in SPUREN, \
        "der Haken mit dem Pfad muss dastehen"
    assert "fremden Rechner" in SPUREN


def test_eintragen_und_wieder_entfernen(programm):
    schtasks = Schtasks()
    planung = WindowsPlanung(programm, laufen=schtasks, windows=True)

    assert planung.zustand().eingetragen is False
    zustand = planung.eintragen("23:00")
    assert zustand.eingetragen is True
    assert zustand.uhrzeit == "23:00"
    assert str(programm) in zustand.pfad

    assert planung.entfernen() is True
    assert planung.zustand().eingetragen is False


def test_ein_eintrag_wird_nur_auf_anweisung_angelegt(programm):
    """Der blosse Blick auf den Zustand darf nichts eintragen."""
    schtasks = Schtasks()
    planung = WindowsPlanung(programm, laufen=schtasks, windows=True)
    planung.zustand()
    planung.zustand()
    assert schtasks.eintrag is None
    assert not any("/Create" in b for b in schtasks.befehle)


def test_ein_eintrag_ins_leere_wird_gar_nicht_erst_angelegt(tmp_path):
    planung = WindowsPlanung(tmp_path / "gibtesnicht.exe",
                             laufen=Schtasks(), windows=True)
    with pytest.raises(RuntimeError) as fehler:
        planung.eintragen("07:00")
    assert "ins Leere" in str(fehler.value)


def test_ein_verwaister_eintrag_wird_erkannt(programm):
    """Der Datentraeger bekommt einen anderen Laufwerksbuchstaben."""
    schtasks = Schtasks()
    planung = WindowsPlanung(programm, laufen=schtasks, windows=True)
    planung.eintragen("07:00")

    programm.unlink()
    zustand = planung.zustand()
    assert zustand.eingetragen is True
    assert zustand.pfad_stimmt is False
    assert "Laufwerksbuchstaben" in zustand.hinweis


def test_entfernen_wird_geprueft_und_nicht_behauptet(programm):
    """schtasks meldet auch dann Erfolg, wenn es nichts zu loeschen gab."""
    class Hartnaeckig(Schtasks):
        def __call__(self, befehl):
            from pkc.aufgaben.windows_planung import _Ergebnis

            if "/Delete" in befehl:
                return _Ergebnis(True, "ERFOLGREICH")   # tut aber nichts
            return super().__call__(befehl)

    planung = WindowsPlanung(programm, laufen=Hartnaeckig(), windows=True)
    planung.eintragen("07:00")
    assert planung.entfernen() is False, \
        "ein 'entfernt', das nichts entfernt hat, waere Scheinerfuellung"


def test_ein_fehlschlag_beim_eintragen_nennt_den_haeufigsten_grund(programm):
    class Verweigert(Schtasks):
        def __call__(self, befehl):
            from pkc.aufgaben.windows_planung import _Ergebnis

            if "/Create" in befehl:
                return _Ergebnis(False, "FEHLER: Zugriff verweigert.")
            return super().__call__(befehl)

    planung = WindowsPlanung(programm, laufen=Verweigert(), windows=True)
    with pytest.raises(RuntimeError) as fehler:
        planung.eintragen("07:00")
    assert "Administratorrechte" in str(fehler.value)
