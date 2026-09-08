"""Der gemeldete Fall der TechMove GmbH - Zahl fuer Zahl.

Diese Tests sind aus einem echten Fehlschlag entstanden. Der
Auftraggeber hat dem Buchhalter eine Fallstudie gegeben, und die Antwort
war in fast jedem Punkt falsch:

* Aus 24.000 EUR wurden 5.995.553,43 EUR.
* Gerechnet wurde mit dem 91. Tag des Kalenderjahres statt mit dem
  16. Tag der Vertragslaufzeit.
* Ein im Maerz angeschafftes Fahrzeug wurde ueber neun Monate
  abgeschrieben statt ueber sieben.
* Eine Rueckstellung sollte in den ARAP - sie ist ein Passivposten.

Die Sollwerte hier stammen nicht von mir. Sie stammen aus der
Musterloesung, die der Auftraggeber mitgeliefert hat, und sind fachlich
nachgerechnet. Wer eine dieser Zahlen aendert, aendert das Ergebnis
einer Bilanz.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pkc.fachrechnen import (abgrenzen, euro, lineare_afa, netto_aus_brutto,
                             pruefe_zahlen, umsatzsteuer_aus_brutto)
from pkc.fachrechnen.abschreibung import monate_zwischen


# -- Umsatzsteuer herausrechnen ---------------------------------------
def test_netto_aus_brutto_wird_geteilt_und_nicht_abgezogen():
    """53.550 brutto sind 45.000 netto - nicht 43.375,50.

    Der haeufigste Fehler ueberhaupt: 19 Prozent vom Bruttobetrag
    abziehen statt durch 1,19 zu teilen. Der Unterschied betraegt hier
    1.624,50 EUR.
    """
    assert netto_aus_brutto(53550, 19) == Decimal("45000.00")
    assert umsatzsteuer_aus_brutto(53550, 19) == Decimal("8550.00")
    # Die falsche Methode zur Abschreckung:
    assert euro(Decimal("53550") * Decimal("0.81")) != netto_aus_brutto(53550)


@pytest.mark.parametrize("satz", [19, 0.19, "19", "19%"])
def test_der_steuersatz_darf_verschieden_geschrieben_werden(satz):
    assert netto_aus_brutto(53550, satz) == Decimal("45000.00")


# -- Abschreibung ------------------------------------------------------
def test_fuhrpark_wird_ueber_sieben_monate_abgeschrieben():
    """Anschaffung 15.03.2026, Stichtag 30.09.2026 - das sind 7 Monate.

    Das Modell hatte 9 gerechnet, weil September der neunte Monat des
    Jahres ist. Der Wagen stand im Januar und Februar aber noch nicht im
    Betrieb.
    """
    afa = lineare_afa(netto_aus_brutto(53550), 5,
                      date(2026, 3, 15), date(2026, 9, 30))
    assert afa.monate == 7, "Maerz bis September sind sieben Monate"
    assert afa.afa_pro_jahr == Decimal("9000.00")
    assert afa.afa_kumuliert == Decimal("5250.00")
    assert afa.buchwert == Decimal("39750.00")


def test_server_wird_ueber_drei_monate_abgeschrieben():
    """Und der Cent stimmt: 1.000,00 EUR, nicht 999,99 EUR.

    4.000 EUR im Jahr sind 333,3333... im Monat. Wer den Monatswert
    zuerst rundet und dann mal drei nimmt, landet bei 999,99.
    """
    afa = lineare_afa(12000, 3, date(2026, 7, 1), date(2026, 9, 30))
    assert afa.monate == 3
    assert afa.afa_kumuliert == Decimal("1000.00")
    assert afa.buchwert == Decimal("11000.00")


def test_der_anschaffungsmonat_zaehlt_voll():
    """§ 7 Abs. 1 EStG: auch bei Anschaffung am Monatsletzten."""
    assert monate_zwischen(date(2026, 3, 31), date(2026, 3, 31)) == 1
    assert monate_zwischen(date(2026, 3, 1), date(2026, 3, 31)) == 1


def test_vor_der_anschaffung_wird_nicht_abgeschrieben():
    afa = lineare_afa(12000, 3, date(2026, 7, 1), date(2026, 6, 30))
    assert afa.monate == 0
    assert afa.afa_kumuliert == Decimal("0.00")
    assert afa.buchwert == Decimal("12000.00")


def test_nach_der_nutzungsdauer_steht_das_gut_bei_null():
    afa = lineare_afa(12000, 3, date(2020, 1, 1), date(2030, 1, 1))
    assert afa.monate == 36
    assert afa.buchwert == Decimal("0.00")


def test_eine_nutzungsdauer_von_null_ist_ein_fehler():
    with pytest.raises(ValueError):
        lineare_afa(12000, 0, date(2026, 1, 1), date(2026, 9, 30))


# -- Abgrenzung --------------------------------------------------------
def test_software_erloese_werden_ab_vertragsbeginn_gerechnet():
    """Der Kern des gemeldeten Fehlers.

    24.000 EUR, Laufzeit 15.09.2026 bis 14.09.2027, Stichtag
    30.09.2026. In die laufende Periode gehoeren 16 Tage, abzugrenzen
    sind 349 Tage - nicht 91 Tage ab Jahresbeginn.
    """
    a = abgrenzen(24000, date(2026, 9, 15), date(2027, 9, 14),
                  date(2026, 9, 30), art="PRAP", basis="tag")
    assert a.einheiten_gesamt == 365
    assert a.einheiten_verbraucht == 16, "15.09. bis 30.09. sind 16 Tage"
    assert a.einheiten_offen == 349
    assert a.betrag_abgrenzung == Decimal("22947.95")
    assert a.betrag_periode == Decimal("1052.05")
    # Und die Probe: die Teile ergeben wieder das Ganze.
    assert a.betrag_periode + a.betrag_abgrenzung == Decimal("24000.00")


def test_versicherung_wird_monatsweise_abgegrenzt():
    """14.400 EUR fuer 12 Monate ab 01.08.2026, Stichtag 30.09.2026.

    Zwei Monate sind verbraucht (August, September), zehn Monate
    gehoeren ins Folgejahr: 12.000 EUR ARAP.
    """
    a = abgrenzen(14400, date(2026, 8, 1), date(2027, 7, 31),
                  date(2026, 9, 30), art="ARAP", basis="monat")
    assert a.einheiten_gesamt == 12
    assert a.einheiten_verbraucht == 2
    assert a.betrag_abgrenzung == Decimal("12000.00")
    assert a.betrag_periode == Decimal("2400.00")


def test_die_summe_stimmt_immer_auf_den_cent():
    """Kein verlorener und kein erfundener Cent - bei keiner Aufteilung."""
    for tage in range(1, 200, 7):
        a = abgrenzen(1000, date(2026, 1, 1), date(2026, 12, 31),
                      date(2026, 1, 1) + __import__("datetime").timedelta(days=tage),
                      art="PRAP", basis="tag")
        assert a.betrag_periode + a.betrag_abgrenzung == Decimal("1000.00")


def test_vor_dem_zeitraum_ist_alles_abzugrenzen():
    a = abgrenzen(1200, date(2026, 10, 1), date(2027, 9, 30),
                  date(2026, 9, 30), art="ARAP", basis="monat")
    assert a.einheiten_verbraucht == 0
    assert a.betrag_abgrenzung == Decimal("1200.00")


def test_nach_dem_zeitraum_ist_nichts_mehr_abzugrenzen():
    a = abgrenzen(1200, date(2025, 1, 1), date(2025, 12, 31),
                  date(2026, 9, 30), art="ARAP", basis="monat")
    assert a.einheiten_offen == 0
    assert a.betrag_abgrenzung == Decimal("0.00")


def test_der_buchungssatz_zeigt_die_richtige_richtung():
    """ARAP mindert Aufwand, PRAP mindert Ertrag - nicht umgekehrt."""
    arap = abgrenzen(1200, date(2026, 1, 1), date(2026, 12, 31),
                     date(2026, 6, 30), art="ARAP", basis="monat")
    prap = abgrenzen(1200, date(2026, 1, 1), date(2026, 12, 31),
                     date(2026, 6, 30), art="PRAP", basis="monat")
    assert "ARAP an Aufwand" in " ".join(arap.rechenweg())
    assert "Ertrag an PRAP" in " ".join(prap.rechenweg())


def test_ein_unbekannter_posten_wird_abgelehnt():
    with pytest.raises(ValueError):
        abgrenzen(1200, date(2026, 1, 1), date(2026, 12, 31),
                  date(2026, 6, 30), art="RUECKSTELLUNG")


# -- Plausibilitaet ----------------------------------------------------
def test_die_sechs_millionen_werden_gefunden():
    """Der Fall, der alles ausgeloest hat."""
    befunde = pruefe_zahlen(
        "Ein Kunde hat am 15.09.2026 eine Jahreslizenz im Voraus bezahlt: "
        "24.000 EUR netto.",
        "Fuer den 30.09.2026 ergibt sich ein periodengerechter Betrag von "
        "5.995.553,43 EUR.")
    assert befunde, "Aus 24.000 koennen keine 5,9 Millionen werden"
    assert "5.995.553,43" in befunde[0].text


def test_richtige_ergebnisse_loesen_keinen_fehlalarm_aus():
    """Ein Waechter, der bei jeder Antwort anschlaegt, wird ignoriert."""
    frage = ("Jahreslizenz 24.000 EUR netto ab 15.09.2026; Versicherung "
             "14.400 EUR netto ab 01.08.2026; Rueckstellung 8.500 EUR.")
    antwort = ("Abzugrenzen sind 22.947,95 EUR (PRAP) und 12.000,00 EUR "
               "(ARAP). Die Rueckstellung betraegt 8.500,00 EUR.")
    assert pruefe_zahlen(frage, antwort) == []


def test_ohne_zahlen_in_der_frage_wird_nicht_geraten():
    """Ohne Massstab kein Verdacht."""
    assert pruefe_zahlen("Was ist ein ARAP?", "Ein ARAP betraegt 900.000 EUR.") == []


def test_summen_ueber_viele_posten_gelten_nicht_als_unmoeglich():
    """Eine Bilanzsumme darf groesser sein als jeder Einzelposten."""
    frage = "Posten von je 50.000 EUR bis 90.000 EUR."
    antwort = "Die Summe betraegt 850.000 EUR."
    assert pruefe_zahlen(frage, antwort) == []
