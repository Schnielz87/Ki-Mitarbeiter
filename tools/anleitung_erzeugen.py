# -*- coding: utf-8 -*-
"""Erzeugt die Bedienungsanleitung als Word-Dokument.

Alle Beschriftungen stammen woertlich aus dem Programmcode
(src/ui/tk_app.py, src/profiles/buchhalter/profile.json) - nicht aus
Erinnerung. Wird die Oberflaeche geaendert, ist dieses Skript erneut zu
laufen bzw. anzupassen.

Braucht python-docx:

    pip install python-docx

Bewusst **nicht** in requirements-dev.txt: die Anwendung braucht es nicht,
der Windows-Bauablauf auch nicht. Das fertige Dokument liegt im Repository,
neu erzeugen muss es nur, wer die Oberflaeche aendert.

    python tools/anleitung_erzeugen.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Cm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from pkc.memory.schema_keys import WELL_KNOWN_KEYS  # noqa: E402

profil = json.loads((REPO / "src/profiles/buchhalter/profile.json").read_text(encoding="utf-8"))

AKZENT = RGBColor(0x1F, 0x4E, 0x79)
GRAU = RGBColor(0x55, 0x55, 0x55)

doc = Document()

# ---------------------------------------------------------------- Formatvorlagen
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(6)

for name, groesse in (("Heading 1", 18), ("Heading 2", 14), ("Heading 3", 12)):
    stil = doc.styles[name]
    stil.font.name = "Calibri"
    stil.font.size = Pt(groesse)
    stil.font.color.rgb = AKZENT
    stil.font.bold = True

for abschnitt in doc.sections:
    abschnitt.top_margin = Cm(2.2)
    abschnitt.bottom_margin = Cm(2.0)
    abschnitt.left_margin = Cm(2.4)
    abschnitt.right_margin = Cm(2.4)


def absatz(text="", stil=None, fett=False, kursiv=False, farbe=None, groesse=None):
    p = doc.add_paragraph(style=stil)
    lauf = p.add_run(text)
    lauf.bold = fett
    lauf.italic = kursiv
    if farbe is not None:
        lauf.font.color.rgb = farbe
    if groesse is not None:
        lauf.font.size = Pt(groesse)
    return p


def punkt(text, ebene=0):
    stil = "List Bullet" if ebene == 0 else "List Bullet 2"
    return doc.add_paragraph(text, style=stil)


def schritt(text):
    return doc.add_paragraph(text, style="List Number")


def kasten(titel, text):
    tabelle = doc.add_table(rows=1, cols=1)
    tabelle.style = "Table Grid"
    zelle = tabelle.rows[0].cells[0]
    p = zelle.paragraphs[0]
    lauf = p.add_run(titel)
    lauf.bold = True
    lauf.font.color.rgb = AKZENT
    zelle.add_paragraph(text)
    doc.add_paragraph()
    return tabelle


def tabelle_mit(kopf, zeilen, breiten=None):
    t = doc.add_table(rows=1, cols=len(kopf))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, text in enumerate(kopf):
        zelle = t.rows[0].cells[i]
        zelle.text = ""
        lauf = zelle.paragraphs[0].add_run(text)
        lauf.bold = True
    for zeile in zeilen:
        zellen = t.add_row().cells
        for i, wert in enumerate(zeile):
            zellen[i].text = ""
            zellen[i].paragraphs[0].add_run(str(wert)).font.size = Pt(10)
    if breiten:
        for zeile in t.rows:
            for i, breite in enumerate(breiten):
                zeile.cells[i].width = Cm(breite)
    doc.add_paragraph()
    return t


# ================================================================ Titelseite
titel = doc.add_paragraph()
titel.alignment = WD_ALIGN_PARAGRAPH.CENTER
lauf = titel.add_run("Portabler KI-Buchhalter")
lauf.bold = True
lauf.font.size = Pt(30)
lauf.font.color.rgb = AKZENT

unter = doc.add_paragraph()
unter.alignment = WD_ALIGN_PARAGRAPH.CENTER
lauf = unter.add_run("Bedienungsanleitung - wo Sie was eingeben")
lauf.font.size = Pt(15)
lauf.font.color.rgb = GRAU

doc.add_paragraph()
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
lauf = info.add_run(f"Programmfassung {profil['version']}  ·  Stand 05.09.2026")
lauf.font.size = Pt(10)
lauf.font.color.rgb = GRAU

doc.add_paragraph()
kasten(
    "Bitte zuerst lesen",
    "Diese Anleitung wird aus dem Programmcode selbst erzeugt. Alle genannten "
    "Registerkarten, Schaltflaechen und Felder tragen daher genau die "
    "Beschriftungen, die das Programm setzt. Der beschriebene Aufbau wurde "
    "am laufenden Programm abgeglichen. Weicht dennoch etwas ab, gilt das "
    "Programm.\n\n"
    "Der Buchhalter ist eine fachliche Zuarbeit. Er ersetzt weder Steuerberater "
    "noch Rechtsanwalt. Verantwortung und Freigabe bleiben immer bei Ihnen.",
)

doc.add_page_break()

# ================================================================ Inhalt
doc.add_heading("Inhalt", level=1)
for nummer, kapitel in enumerate([
    "In fuenf Minuten startklar",
    "Der Startbildschirm - was er Ihnen sagt",
    "Der Bildschirm: fuenf Registerkarten",
    "Schritt 1 - Ihr Unternehmen einrichten",
    "Schritt 2 - Fragen stellen",
    "Wie eine Antwort aufgebaut ist",
    "Was automatisch gespeichert wird - und was nicht",
    "Belege hinzufuegen",
    "Unternehmenswissen pflegen",
    "Wissen aktualisieren",
    "Einstellungen und Status",
    "Lizenz",
    "Was der Buchhalter nicht tut",
    "Wenn etwas nicht funktioniert",
], start=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.add_run(f"{nummer}.  ").bold = True
    p.add_run(kapitel)

doc.add_page_break()

# ================================================================ 1
doc.add_heading("1.  In fuenf Minuten startklar", level=1)

absatz("Der Buchhalter liegt vollstaendig auf Ihrem Datentraeger. Er braucht "
       "keine Installation, keine Administratorrechte und kein Internet.")

doc.add_heading("So starten Sie", level=2)
schritt("Datentraeger (SSD, USB-Stick) an den Windows-PC anschliessen.")
schritt("Den Ordner oeffnen.")
schritt("PORTABLE_BUCHHALTER.exe doppelklicken.")
schritt("Es oeffnet sich ein kleines Fenster mit der Ueberschrift PORTABLER "
        "BUCHHALTER und einer Systempruefung. Warten Sie, bis die Pruefung "
        "durchgelaufen ist.")
schritt("Steht dort \"Der Buchhalter kann gestartet werden\", klicken Sie auf "
        "die Schaltflaeche BUCHHALTER STARTEN. Erst dann ist sie anklickbar.")

absatz()
kasten(
    "Beim allerersten Start",
    "Windows meldet sich mit \"Der Computer wurde durch Windows geschuetzt\". "
    "Das liegt daran, dass die Anwendung noch nicht digital signiert ist - es "
    "ist kein Fehler. Klicken Sie auf \"Weitere Informationen\" und dann auf "
    "\"Trotzdem ausfuehren\".",
)

doc.add_heading("Der Laufwerksbuchstabe ist egal", level=2)
absatz("Ob der Datentraeger als D:, E: oder F: erscheint, spielt keine Rolle. "
       "Der Buchhalter findet seine Daten selbst. Auch Pfade mit Leerzeichen "
       "funktionieren. Sie koennen den Datentraeger an einen anderen PC "
       "stecken - Ihr Unternehmenswissen und Ihre Unterhaltungen sind dort "
       "unveraendert vorhanden, weil alles auf dem Datentraeger liegt und "
       "nichts auf dem jeweiligen Rechner.")

# ================================================================ 2
doc.add_heading("2.  Der Startbildschirm - was er Ihnen sagt", level=1)

absatz("Bevor der Buchhalter startet, prueft er sich selbst und zeigt das "
       "Ergebnis an. Das ist keine Formalie: Sie sehen dort, ob er "
       "arbeitsfaehig ist und was ihm gegebenenfalls fehlt. Jede Zeile hat "
       "ein Ergebnis - OK oder HINWEIS.")

tabelle_mit(
    ["Zeile", "Was geprueft wird", "Was Sie sehen sollten"],
    [
        ["Datenverzeichnis",
         "Wo Ihre Daten liegen und ob dorthin geschrieben werden kann",
         "OK, dahinter der Pfad und \"(beschreibbar)\""],
        ["Unternehmensgedaechtnis",
         "Wie viele Angaben ueber Ihren Betrieb gespeichert sind",
         "OK, Anzahl der Eintraege, \"Integritaet: ok\""],
        ["Fachwissen",
         "Die mitgelieferten Fachmodule",
         "OK, 13 Dokumente, 57 Abschnitte"],
        ["Suchindex",
         "Ob die Suche ueber das Fachwissen einsatzbereit ist",
         "OK, Anzahl der Abschnitte"],
        ["Lokales Modell",
         "Ob ein Sprachmodell vorhanden ist",
         "HINWEIS, solange keines eingerichtet ist - siehe unten"],
        ["Lizenz",
         "Ob eine Lizenz noetig und gueltig ist",
         "OK - siehe Kapitel 12"],
        ["Quellenregister",
         "Die hinterlegten amtlichen Quellen",
         "OK, 12 Quellen, 32 Dokumente"],
        ["Geheimnistresor",
         "Der verschluesselte Speicher fuer Passwoerter und Zugaenge",
         "OK, \"noch nicht angelegt\" ist voellig in Ordnung"],
    ],
    breiten=[3.8, 5.8, 5.4],
)

absatz("Darunter stehen vier Angaben zum Zustand:")
punkt("Wissensstand - auf welchem Datum die gespeicherten Fachquellen stehen.")
punkt("Internet - ob eine Verbindung besteht. Fuer die taegliche Arbeit "
      "unerheblich; gebraucht wird sie nur zum Nachladen von Quellen.")
punkt("Betriebsart - OFFLINE oder HYBRID. HYBRID heisst lediglich, dass "
      "Internet verfuegbar ist. Gearbeitet wird trotzdem lokal.")
punkt("Datenverzeichnis - der Ordner auf Ihrem Datentraeger.")

absatz()
absatz("Steht am Ende \"Der Buchhalter kann gestartet werden.\", ist alles "
       "in Ordnung. Erst dann laesst sich die Schaltflaeche BUCHHALTER "
       "STARTEN anklicken.", fett=True)

doc.add_heading("HINWEIS ist kein Fehler", level=2)
absatz("OK bedeutet: in Ordnung. HINWEIS bedeutet: es fehlt etwas, aber der "
       "Buchhalter laeuft trotzdem. Der haeufigste Fall ist das Sprachmodell:")

kasten(
    "\"Lokales Modell: HINWEIS - Kein Sprachmodell verfuegbar\"",
    "Das ist der Normalzustand, solange Sie kein Modell eingerichtet haben. "
    "Der Buchhalter laeuft dann im sogenannten Notbetrieb: er recherchiert "
    "in seinen Quellen und zeigt Ihnen die Fundstellen, formuliert aber "
    "keine ausformulierte Fachantwort.\n\n"
    "Das ist Absicht. Lieber sagt er ehrlich, dass er nichts formulieren "
    "kann, als etwas zu erfinden. Wie Sie ein Modell einrichten, steht in "
    "docs/MODELL_EINRICHTEN.md - einmalig, etwa 5 GB.",
)

absatz("Ein echter Fehler wuerde die Zeile mit FEHLER kennzeichnen und die "
       "Schaltflaeche BUCHHALTER STARTEN gesperrt lassen.")

# ================================================================ 3
doc.add_heading("3.  Der Bildschirm: fuenf Registerkarten", level=1)
absatz("Nach dem Start sehen Sie oben eine Zeile mit fuenf Registerkarten. "
       "Alles, was Sie tun, geschieht in einer davon.")

tabelle_mit(
    ["Registerkarte", "Wofuer", "Was Sie dort eingeben"],
    [
        ["Unterhaltung", "Fragen stellen und Antworten lesen",
         "Ihre Frage in das grosse Eingabefeld unten links"],
        ["Unternehmenswissen", "Angaben zu Ihrem Betrieb dauerhaft speichern",
         "Suchbegriffe oben; Angaben ueber \"Neu / Aendern\" oder \"Onboarding fortsetzen\""],
        ["Belege", "Eigene Dokumente einlesen",
         "Keine Eingabe - Sie waehlen ueber \"Beleg hinzufuegen\" eine Datei aus"],
        ["Wissen aktualisieren", "Amtliche Quellen nachladen (braucht Internet)",
         "Keine Eingabe - nur Schaltflaechen"],
        ["Einstellungen und Status", "Verhalten einstellen, Zustand pruefen",
         "Auswahllisten und Haekchen"],
    ],
    breiten=[3.6, 5.4, 7.0],
)

absatz("Ganz oben rechts stehen zwei Angaben, die Sie im Blick behalten "
       "sollten:")
punkt("Betriebsart - OFFLINE oder HYBRID. HYBRID heisst nur, dass Internet "
      "verfuegbar ist; gearbeitet wird trotzdem lokal.")
punkt("Wissensstand - das Datum, auf dem die gespeicherten Fachquellen stehen.")
absatz("Ganz unten laeuft eine Statuszeile mit, die auch den Pfad Ihres "
       "Datentraegers nennt.")

# ================================================================ 3
doc.add_heading("4.  Schritt 1 - Ihr Unternehmen einrichten", level=1)

absatz("Das ist das Erste, was Sie tun sollten. Der Buchhalter arbeitet umso "
       "besser, je mehr er ueber Ihren Betrieb weiss - und er merkt es sich "
       "dauerhaft auf dem Datentraeger.")

doc.add_heading("Der gefuehrte Weg", level=2)
schritt("Registerkarte Unternehmenswissen oeffnen.")
schritt("Unten auf Onboarding fortsetzen klicken.")
schritt("Es oeffnet sich das Fenster Unternehmens-Onboarding mit einer Liste "
        "von Fragen. Links steht die Frage, rechts ein Eingabefeld.")
schritt("Ausfuellen, was Sie wissen. Alles darf leer bleiben und spaeter "
        "ergaenzt werden.")
schritt("Auf Speichern klicken.")

absatz("Oben rechts in der Registerkarte sehen Sie danach den Fortschritt, "
       "zum Beispiel \"Onboarding: 7 von 21 beantwortet\".")

doc.add_heading("Diese Angaben werden abgefragt", level=2)
absatz("Die Reihenfolge im Fenster entspricht dieser Liste.")

zeilen = []
for schluessel in profil["onboarding_keys"]:
    meta = WELL_KNOWN_KEYS.get(schluessel, {"title": schluessel, "category": ""})
    zeilen.append([meta["title"], meta.get("category", "")])
tabelle_mit(["Angabe", "Kategorie"], zeilen, breiten=[8.0, 4.0])

kasten(
    "Sie koennen es auch einfach sagen",
    "Statt das Formular auszufuellen, duerfen Sie solche Angaben auch mitten "
    "im Gespraech nennen - zum Beispiel: \"Wir verwenden grundsaetzlich "
    "SKR03.\" Der Buchhalter erkennt dauerhaft gueltige Unternehmensangaben "
    "und fragt nach, ob er sie sich merken soll. Ob er nachfragt oder still "
    "speichert, stellen Sie unter Einstellungen ein.",
)

# ================================================================ 4
doc.add_heading("5.  Schritt 2 - Fragen stellen", level=1)

absatz("Registerkarte Unterhaltung. Der Bildschirm ist geteilt:")
punkt("Links oben: der bisherige Gespraechsverlauf.")
punkt("Links unten: das Eingabefeld - hier tippen Sie Ihre Frage.")
punkt("Rechts oben: Quellen der letzten Antwort - die Fundstellen, auf die "
      "sich die Antwort stuetzt.")
punkt("Rechts unten: Unterhaltungen - Ihre frueheren Gespraeche zum "
      "Nachschlagen.")

doc.add_heading("So fragen Sie", level=2)
schritt("In das Eingabefeld unten links klicken.")
schritt("Frage eintippen. Mehrere Zeilen sind erlaubt.")
schritt("Auf Absenden klicken - oder Strg + Eingabetaste druecken. Die "
        "Eingabetaste allein macht nur einen Zeilenumbruch.")

absatz()
doc.add_heading("Weitere Schaltflaechen daneben", level=2)
tabelle_mit(
    ["Schaltflaeche", "Was sie tut"],
    [
        ["Absenden", "Schickt Ihre Frage ab"],
        ["Neue Unterhaltung", "Beginnt ein neues Gespraech; das alte bleibt rechts erhalten"],
        ["Dokument hinzufuegen", "Liest einen Beleg ein, auf den Sie sich dann beziehen koennen"],
        ["Unterhaltung exportieren", "Speichert das Gespraech als lesbare Datei auf dem Datentraeger"],
    ],
    breiten=[5.0, 10.0],
)

doc.add_heading("Gute Fragen", level=2)
absatz("Je konkreter, desto besser. Beispiele:")
punkt("\"Welche Pflichtangaben muss eine Rechnung enthalten?\"")
punkt("\"Ein Lieferant aus Polen stellt uns ohne Umsatzsteuer in Rechnung. "
      "Wie buchen wir das?\"")
punkt("\"Wie lange muessen wir Eingangsrechnungen aufbewahren?\"")
punkt("\"Wir haben einen Firmenwagen geleast. Welche Unterlagen brauchen wir "
      "fuer den Jahresabschluss?\"")

# ================================================================ 5
doc.add_heading("6.  Wie eine Antwort aufgebaut ist", level=1)

absatz("Der Buchhalter antwortet nach einem festen Schema. Nicht jeder "
       "Abschnitt kommt bei jeder Frage vor, aber die Reihenfolge ist immer "
       "gleich:")

beschreibungen = {
    "ERGEBNIS": "Die kurze Antwort - was gilt.",
    "BEGRUENDUNG": "Warum das so ist.",
    "STEUERLICHE BEHANDLUNG": "Die steuerliche Seite des Sachverhalts.",
    "BUCHHALTERISCHE BEHANDLUNG": "Die buchhalterische Seite.",
    "BUCHUNGSVORSCHLAG": "Ein Vorschlag - Soll an Haben. Nur ein Vorschlag, siehe Freigabebedarf.",
    "BENOETIGTE UNTERLAGEN": "Was Sie noch beschaffen muessen.",
    "OFFENE PUNKTE": "Was der Buchhalter nicht klaeren konnte.",
    "RISIKEN": "Worauf Sie achten sollten.",
    "QUELLEN": "Die Fundstellen, nummeriert. Diese Nummern koennen Sie rechts nachschlagen.",
    "WISSENSSTAND": "Auf welchem Stand die verwendeten Quellen sind und wodurch die Antwort entstand.",
    "FREIGABEBEDARF": "Was ein Mensch freigeben muss, bevor es wirksam wird.",
}
tabelle_mit(
    ["Abschnitt", "Bedeutung"],
    [[a, beschreibungen.get(a, "")] for a in profil["answer_sections"]],
    breiten=[6.0, 9.0],
)

kasten(
    "Wichtig: die Abschnitte QUELLEN und FREIGABEBEDARF",
    "QUELLEN ist die Kontrolle. Der Buchhalter muss belegen, worauf er sich "
    "stuetzt. Steht dort nichts Brauchbares, ist die Antwort nicht belastbar - "
    "auch wenn sie ueberzeugend klingt.\n\n"
    "FREIGABEBEDARF sagt Ihnen, was noch nicht erledigt ist. Ein "
    "Buchungsvorschlag ist ein Vorschlag, keine Buchung.",
)

doc.add_heading("Wenn kein Sprachmodell eingerichtet ist", level=2)
absatz("Dann schreibt der Buchhalter offen: \"Hinweis: Es wurde keine "
       "Modellantwort erzeugt.\" Er recherchiert trotzdem in seinen Quellen "
       "und zeigt Ihnen die Fundstellen - er formuliert nur keine fachliche "
       "Wuerdigung. Das ist gewollt: lieber ehrlich nichts sagen als etwas "
       "erfinden. Die Einrichtung eines Sprachmodells ist in "
       "docs/MODELL_EINRICHTEN.md beschrieben (einmalig, etwa 5 GB).")

# ================================================================ 7
doc.add_heading("7.  Was automatisch gespeichert wird - und was nicht", level=1)

absatz("Die wichtigste Frage im taeglichen Umgang. Kurz: Ihre Unterhaltungen "
       "werden automatisch gespeichert. Alles, was in Ihr "
       "Unternehmensgedaechtnis soll, bestaetigen Sie ausdruecklich.")

tabelle_mit(
    ["Was", "Speichert sich das von selbst?", "Was Sie tun muessen"],
    [
        ["Ihre Frage und die Antwort",
         "Ja, sofort",
         "Nichts. Jede Frage und jede Antwort wird in dem Moment auf den "
         "Datentraeger geschrieben, in dem sie entsteht."],
        ["Die Unterhaltung als Ganzes",
         "Ja",
         "Nichts. Sie erscheint rechts unter \"Unterhaltungen\" und ist nach "
         "einem Neustart wieder da."],
        ["Angaben, die Sie im Gespraech nennen",
         "Nein - es wird gefragt",
         "Erkennt der Buchhalter eine dauerhafte Unternehmensangabe, fragt "
         "er \"Dauerhaft merken?\". Erst mit Ja wird gespeichert."],
        ["Onboarding-Fragebogen",
         "Nein",
         "Auf Speichern klicken."],
        ["Eintrag unter Neu / Aendern",
         "Nein",
         "Auf Speichern klicken."],
        ["Einstellungen",
         "Nein",
         "Auf Einstellungen speichern klicken."],
        ["Beleg",
         "Ja, beim Auswaehlen",
         "Nichts weiter. Die Datei wird sofort auf den Datentraeger "
         "uebernommen."],
    ],
    breiten=[3.8, 3.6, 7.6],
)

kasten(
    "Es gibt keine Schaltflaeche \"Alles speichern\"",
    "Und Sie brauchen auch keine. Der Buchhalter schreibt jede Aenderung "
    "sofort und einzeln auf den Datentraeger - nicht erst beim Beenden. "
    "Selbst wenn der Rechner mitten in der Arbeit ausgeht, ist alles bis zur "
    "letzten abgeschickten Frage vorhanden.",
)

doc.add_heading("Wo das alles liegt", level=2)
absatz("Ausschliesslich auf Ihrem Datentraeger, unterhalb des Ordners, den "
       "der Startbildschirm als Datenverzeichnis nennt - bei Ihnen zum "
       "Beispiel E:\\Portable-Buchhalter-Windows. Nichts wird auf dem "
       "jeweiligen PC abgelegt, nichts in die Windows-Registrierung "
       "geschrieben, nichts hochgeladen, nichts an Dritte gesendet. Deshalb "
       "koennen Sie den Datentraeger abziehen, an einem anderen Rechner "
       "einstecken und dort weiterarbeiten.")

absatz("Diese Ordner liegen dort - Sie duerfen jederzeit hineinschauen:")

tabelle_mit(
    ["Ordner", "Was darin liegt", "Ihre Daten?"],
    [
        ["database", "Die Datenbank company.db: Unternehmensgedaechtnis, "
                     "alle Unterhaltungen, das Protokoll", "Ja - das Wichtigste"],
        ["company", "Das Unternehmensprofil in lesbarer Form, sobald Sie es "
                    "exportieren", "Ja"],
        ["conversations", "Exportierte Unterhaltungen", "Ja"],
        ["workspace", "Ihre eigenen Arbeitsdateien und aufgenommenen Belege", "Ja"],
        ["backups", "Sicherungen, die Sie angelegt haben", "Ja"],
        ["logs", "Protokolldateien, darunter startfehler.txt", "Betriebsdaten"],
        ["config", "Ihre Einstellungen (settings.json), das Quellenregister "
                   "und der verschluesselte Tresor (secrets.enc)", "Ja"],
        ["license", "Die Lizenzdateien, sobald es welche gibt", "Vertragsdaten"],
        ["resources", "Die abgerufenen amtlichen Quellen und der Suchindex", "Fachwissen"],
        ["knowledge", "Die mitgelieferten Fachmodule", "Programmbestandteil"],
        ["models", "Das Sprachmodell, sobald Sie eines einrichten", "Programmbestandteil"],
        ["updates", "Sicherung und Bericht je Wissensupdate (fuer die Ruecknahme)", "Betriebsdaten"],
        ["src, tools, docs", "Das Programm selbst und die Unterlagen", "Programmbestandteil"],
    ],
    breiten=[3.4, 8.6, 3.2],
)

kasten(
    "Die eine Datei, auf die es ankommt",
    "database\\company.db. Darin steht alles, was der Buchhalter ueber Ihr "
    "Unternehmen weiss, samt Verlauf und allen Unterhaltungen. Wenn Sie nur "
    "eine Sache sichern wollen, dann diese - besser aber ueber die "
    "Schaltflaeche Sicherung erstellen, weil dabei auch eine Beschreibung "
    "des Inhalts mitgeschrieben wird.",
)

doc.add_heading("Mehrere Unternehmen auf einem Datentraeger", level=2)
absatz("Betreuen Sie mehrere Firmen, kann der Buchhalter getrennte "
       "Kundenbereiche fuehren. Die oben genannten Ordner liegen dann "
       "unterhalb von customers\\<Kennung>\\ - je Kunde ein eigener Baum. "
       "Unternehmenswissen des einen Kunden kann so nicht beim anderen "
       "auftauchen. Das allgemeine Fachwissen bleibt bewusst gemeinsam, denn "
       "es enthaelt keine Unternehmensdaten.")

doc.add_heading("Trotzdem: Sicherungen", level=2)
absatz("Automatisches Speichern schuetzt nicht vor einem Defekt des "
       "Datentraegers. Legen Sie regelmaessig eine Sicherung an - "
       "Registerkarte Wissen aktualisieren, Schaltflaeche Sicherung "
       "erstellen - und bewahren Sie sie an einem anderen Ort auf.")

# ================================================================ 8
doc.add_heading("8.  Belege hinzufuegen", level=1)

absatz("Sie koennen eigene Dokumente einlesen - Rechnungen, Vertraege, "
       "Kontoauszuege als Text. Der Buchhalter kann sich dann in seinen "
       "Antworten darauf beziehen.")

schritt("Registerkarte Belege oeffnen (oder in der Unterhaltung auf "
        "\"Dokument hinzufuegen\" klicken - beides fuehrt zum selben).")
schritt("Auf Beleg hinzufuegen klicken.")
schritt("Datei auswaehlen. Unterstuetzt werden: PDF, TXT, MD, HTML, HTM, XML, CSV.")
schritt("Der Beleg erscheint in der Liste mit Titel, Art, Zeitpunkt, Status "
        "und der Ablage auf dem Datentraeger.")

kasten(
    "Wo der Beleg landet",
    "Auf Ihrem Datentraeger, nirgendwo sonst. Die Spalte \"Ablage auf dem "
    "Datentraeger\" nennt den genauen Pfad. Es wird nichts hochgeladen und "
    "nichts an Dritte gesendet.",
)

# ================================================================ 7
doc.add_heading("9.  Unternehmenswissen pflegen", level=1)

absatz("Registerkarte Unternehmenswissen. Hier steht alles, was sich der "
       "Buchhalter ueber Ihren Betrieb gemerkt hat - versioniert, mit "
       "Verlauf.")

doc.add_heading("Die Tabelle", level=2)
tabelle_mit(
    ["Spalte", "Bedeutung"],
    [
        ["Schluessel", "Der technische Name, z. B. company.chart_of_accounts"],
        ["Kategorie", "Einordnung, z. B. accounting, tax, process"],
        ["Titel", "Die verstaendliche Bezeichnung, z. B. Kontenrahmen"],
        ["Inhalt", "Was gespeichert ist"],
        ["V", "Version - wie oft dieser Eintrag geaendert wurde"],
    ],
    breiten=[4.0, 11.0],
)

doc.add_heading("Suchen", level=2)
absatz("Oben links steht das Feld Suche. Suchbegriff eintippen und auf Suchen "
       "klicken oder die Eingabetaste druecken. Alles anzeigen setzt die "
       "Suche zurueck.")

doc.add_heading("Eintrag anlegen oder aendern", level=2)
absatz("Auf Neu / Aendern klicken. Es oeffnet sich das Fenster "
       "\"Unternehmenswissen bearbeiten\" mit vier Feldern:")
tabelle_mit(
    ["Feld", "Was hineingehoert"],
    [
        ["Schluessel", "Kurzer technischer Name ohne Leerzeichen, z. B. company.bank"],
        ["Titel", "Verstaendliche Bezeichnung, z. B. Hausbank"],
        ["Kategorie", "Einordnung, z. B. accounting, tax, process, profile"],
        ["Inhalt", "Der eigentliche Text - hier steht, was gilt"],
    ],
    breiten=[4.0, 11.0],
)
absatz("Zum Aendern eines vorhandenen Eintrags diesen zuerst in der Tabelle "
       "anklicken, dann Neu / Aendern. Die alte Fassung geht nicht verloren.")

doc.add_heading("Die uebrigen Schaltflaechen", level=2)
tabelle_mit(
    ["Schaltflaeche", "Was sie tut"],
    [
        ["Verlauf", "Zeigt alle frueheren Fassungen des markierten Eintrags"],
        ["Archivieren", "Nimmt den Eintrag aus dem aktiven Bestand; er bleibt im Verlauf erhalten"],
        ["Onboarding fortsetzen", "Oeffnet den gefuehrten Fragebogen aus Kapitel 4"],
        ["Profil exportieren", "Schreibt das gesamte Unternehmensprofil als lesbare Datei auf den Datentraeger"],
    ],
    breiten=[5.0, 10.0],
)

kasten(
    "Was hier nicht hineingehoert",
    "Keine Passwoerter, keine Zugangsdaten, keine Schluessel. Dafuer gibt es "
    "einen verschluesselten Tresor. Das Unternehmensgedaechtnis ist "
    "unverschluesselter Klartext auf dem Datentraeger - das ist Absicht, "
    "damit Sie es jederzeit lesen und pruefen koennen.",
)

# ================================================================ 8
doc.add_heading("10.  Wissen aktualisieren", level=1)

absatz("Registerkarte Wissen aktualisieren. Hier laedt der Buchhalter "
       "amtliche Quellen nach. Das ist der einzige Teil, der Internet "
       "braucht. Ohne Internet wird nichts abgerufen, und der vorhandene "
       "Wissensstand bleibt unveraendert nutzbar.")

tabelle_mit(
    ["Schaltflaeche", "Was sie tut", "Wann sinnvoll"],
    [
        ["Wissen jetzt aktualisieren", "Laedt die Quellen und uebernimmt sie",
         "Wenn Sie online sind und den Stand auffrischen wollen"],
        ["Trockenlauf (nichts schreiben)", "Zeigt, was passieren wuerde, ohne etwas zu aendern",
         "Zum Ausprobieren, wenn Sie unsicher sind"],
        ["Letzten Lauf zuruecknehmen", "Macht das letzte Update rueckgaengig",
         "Wenn nach einem Update etwas nicht stimmt"],
        ["Sicherung erstellen", "Legt eine Sicherungskopie Ihrer Daten an",
         "Vor groesseren Aenderungen - und regelmaessig"],
    ],
    breiten=[4.6, 6.4, 5.0],
)

kasten(
    "Sicherungen gehoeren nicht auf denselben Datentraeger",
    "Geht die SSD verloren oder kaputt, ist eine Sicherung darauf ebenfalls "
    "weg. Legen Sie Sicherungen zusaetzlich woanders ab - zweite Festplatte, "
    "Netzlaufwerk. Der Buchhalter unterstuetzt das ausdruecklich.",
)

# ================================================================ 9
doc.add_heading("11.  Einstellungen und Status", level=1)

absatz("Registerkarte Einstellungen und Status. Links stellen Sie ein, rechts "
       "sehen Sie den Zustand.")

doc.add_heading("Die Einstellungen (links)", level=2)
tabelle_mit(
    ["Einstellung", "Auswahl", "Bedeutung"],
    [
        ["Zeitplan Wissensupdate", "manual, weekly, monthly, custom",
         "Wie oft an ein Update erinnert wird. manual = nur wenn Sie es anstossen"],
        ["Fundstellen je Antwort", "4, 6, 8, 12, 16",
         "Wie viele Quellen herangezogen werden. Mehr = gruendlicher, aber langsamer"],
        ["Dauerhafte Unternehmensinformationen erkennen", "Haekchen",
         "Erkennt im Gespraech genannte Angaben zu Ihrem Betrieb"],
        ["Vor dem Speichern nachfragen", "Haekchen",
         "Fragt nach, bevor etwas ins Unternehmensgedaechtnis kommt. Empfohlen: an"],
        ["Online-Sprachmodell erlauben (optional)", "Haekchen",
         "Erlaubt die Nutzung eines Modells im Internet. Standard: aus"],
        ["Protokollierung aktiv", "Haekchen",
         "Zeichnet auf, was geschehen ist. Empfohlen: an - das ist Ihr Nachweis"],
    ],
    breiten=[5.0, 3.4, 7.6],
)
absatz("Aenderungen werden erst mit Einstellungen speichern wirksam.")

doc.add_heading("Der Status (rechts)", level=2)
absatz("Zeigt dieselbe Uebersicht wie beim Start: Datenverzeichnis, "
       "Unternehmensgedaechtnis, Fachwissen, Suchindex, lokales Modell, "
       "Lizenz, Quellenregister, Geheimnistresor. Mit Status aktualisieren "
       "wird neu geprueft.")
absatz("Steht bei einem Punkt HINWEIS statt OK, ist das kein Fehler, sondern "
       "eine Einschraenkung - etwa \"Kein Sprachmodell verfuegbar\". Der Text "
       "daneben sagt, was das bedeutet und wie es zu beheben ist.")

# ================================================================ 12
doc.add_heading("12.  Lizenz", level=1)

doc.add_heading("Im Augenblick muessen Sie nichts tun", level=2)
absatz("Der Startbildschirm zeigt in der Zeile Lizenz:")
absatz("\"Diese Fassung laeuft ohne Lizenzpruefung (Vorab- bzw. "
       "Pilotfassung).\"", kursiv=True)
absatz("Genau so ist es gemeint. Diese Fassung braucht keine Lizenzdatei, "
       "keine Aktivierung, keinen Schluessel und keine Registrierung. Sie "
       "koennen sofort arbeiten.")

doc.add_heading("Warum das so ist", level=2)
absatz("Die Lizenzpruefung ist vollstaendig eingebaut und geprueft, aber "
       "bewusst noch nicht scharf geschaltet. Dazu fehlt ein Stueck, das "
       "nicht in der Software liegen kann: der oeffentliche Pruefschluessel "
       "des Herausgebers. Solange der nicht eingebaut ist, taeuscht die "
       "Anwendung keine Gueltigkeit vor - sie sagt offen, dass sie nicht "
       "pruefen kann. Das ist der ehrlichere Zustand als eine Pruefung, die "
       "nur so tut.")

doc.add_heading("Wie es spaeter funktionieren wird", level=2)
absatz("Damit Sie wissen, was auf Sie zukommt:")
schritt("Sie erhalten eine Lizenzdatei - zwei kleine Dateien, license.json "
        "und license.sig - und legen sie in den Ordner license auf dem "
        "Datentraeger.")
schritt("Beim Start prueft der Buchhalter die Signatur. Das geschieht "
        "vollstaendig ohne Internet; es wird nichts uebertragen und nichts "
        "gemeldet.")
schritt("Die Lizenz ist an den Datentraeger gebunden, nicht an einen "
        "bestimmten PC. Sie koennen die SSD also weiterhin an jeden Rechner "
        "stecken - genau das soll erhalten bleiben.")

absatz()
tabelle_mit(
    ["Fall", "Was dann passiert"],
    [
        ["Sie kopieren den Ordner auf einen zweiten Datentraeger",
         "Die Kopie ist nicht lizenziert. Das Original bleibt gueltig."],
        ["Jemand aendert die Lizenzdatei",
         "Die Signatur passt nicht mehr, die Lizenz wird abgelehnt."],
        ["Kein Internet",
         "Ohne Bedeutung - die Pruefung laeuft rein oertlich."],
        ["Der Datentraeger geht kaputt",
         "Sie erhalten fuer den Ersatz eine neue Lizenz. Ein vorgesehener, "
         "getesteter Vorgang."],
        ["Die Lizenz fehlt oder ist ungueltig",
         "Sie bekommen eine verstaendliche Meldung. Ihre Daten bleiben "
         "unangetastet - siehe unten."],
    ],
    breiten=[6.2, 8.8],
)

kasten(
    "Ihre Daten werden nie als Druckmittel benutzt",
    "Fehlt die Lizenz oder ist sie ungueltig, wird nichts geloescht, nichts "
    "gesperrt und nichts verschluesselt. Ihr Unternehmenswissen bleibt "
    "lesbar, und Export und Sicherung funktionieren weiter. Eine "
    "Lizenzfrage ist eine kaufmaennische Angelegenheit und darf sich nie "
    "gegen Ihre Daten richten.",
)

doc.add_heading("Was noch fehlt, damit die Lizenzierung greift", level=2)
absatz("Damit Sie den Aufwand einschaetzen koennen - technisch ist alles "
       "vorhanden und geprueft, es fehlen im Wesentlichen zwei "
       "Entscheidungen und ein Schluesselpaar:")

tabelle_mit(
    ["Schritt", "Was zu tun ist", "Wer"],
    [
        ["1. Schluesselpaar erzeugen",
         "Einmalig ein Ed25519-Schluesselpaar erzeugen. Der private "
         "Schluessel bleibt beim Herausgeber und darf den Betrieb nie "
         "verlassen; wer ihn hat, kann beliebige Lizenzen ausstellen.",
         "Herausgeber"],
        ["2. Oeffentlichen Schluessel einbauen",
         "Der oeffentliche Teil wird in die Anwendung uebernommen. Nur er "
         "wird ausgeliefert - er kann Lizenzen pruefen, aber keine "
         "ausstellen.",
         "Entwicklung"],
        ["3. Lizenzpflicht einschalten",
         "In der Konfiguration license.required auf true setzen. Bis dahin "
         "laeuft die Pilotfassung bewusst ohne Pruefung.",
         "Entscheidung"],
        ["4. Lizenzmodell festlegen",
         "Laufzeit, Zahl der Instanzen, enthaltene Fachmodule. Das steht "
         "spaeter in der Lizenzdatei.",
         "Kaufmaennisch"],
        ["5. Programm signieren",
         "Ein Code-Signing-Zertifikat beschaffen und die EXE signieren. "
         "Danach entfaellt die SmartScreen-Meldung beim ersten Start.",
         "Herausgeber"],
    ],
    breiten=[3.6, 8.4, 3.0],
)

absatz("Die Punkte 1 bis 4 sind Einrichtung, kein Programmierauftrag - das "
       "Verfahren selbst ist fertig und mit 22 Tests abgesichert, "
       "einschliesslich aller Faelle: Kopie auf einen zweiten Datentraeger, "
       "veraenderte Lizenzdatei, fehlende Signatur, Ablauf, Ersatzgeraet.")

doc.add_heading("Der Ablauf im Betrieb, wenn es soweit ist", level=2)
absatz("Fuer Sie als Anwender bleibt es einfach:")
schritt("Aktivierungsanfrage erzeugen: "
        "PORTABLE_BUCHHALTER_KONSOLE.exe lizenz anfrage --kunde \"Ihre Firma\" "
        "--datei anfrage.json. Darin steht die Kennung des Datentraegers, "
        "keine Unternehmensdaten.")
schritt("Die Datei an den Herausgeber schicken.")
schritt("Sie erhalten license.json und license.sig zurueck.")
schritt("Aufnehmen: PORTABLE_BUCHHALTER_KONSOLE.exe lizenz aufnehmen "
        "--lizenz license.json --signatur license.sig. Die Dateien landen "
        "im Ordner license auf dem Datentraeger.")
schritt("Pruefen: PORTABLE_BUCHHALTER_KONSOLE.exe lizenz - zeigt den Zustand "
        "an. Ab dann steht er auch im Startbildschirm.")

absatz("Es wird dabei zu keinem Zeitpunkt etwas ins Internet uebertragen.")

kasten(
    "Solange der Pruefschluessel fehlt",
    "Die Schritte funktionieren schon heute - eine Lizenz laesst sich "
    "erzeugen und aufnehmen. Der Buchhalter meldet dann aber ehrlich "
    "\"NICHT_PRUEFBAR: In dieser Fassung ist kein Pruefschluessel des "
    "Herausgebers hinterlegt. Die Lizenz wird deshalb weder als gueltig noch "
    "als ungueltig behandelt.\" Er tut also nicht so, als haette er "
    "geprueft. Mit eingebautem Schluessel wird daraus GUELTIG.",
)

doc.add_heading("Und die Software selbst?", level=2)
absatz("Diese Fassung ist eine Vorab- bzw. Pilotfassung. Sie ist noch nicht "
       "digital signiert - daher die Windows-Meldung beim ersten Start - und "
       "sie ist nicht als kommerziell freigegeben erklaert. Was dafuer noch "
       "fehlt, koennen Sie sich jederzeit selbst anzeigen lassen: "
       "PORTABLE_BUCHHALTER_KONSOLE.exe reife")

# ================================================================ 13
doc.add_heading("13.  Was der Buchhalter nicht tut", level=1)

absatz("Das ist kein Mangel, sondern bewusst so gebaut. Bitte lesen Sie es "
       "einmal in Ruhe.")

for grenze in profil["limits"]:
    punkt(grenze)

absatz()
doc.add_heading("Diese Vorgaenge brauchen immer Ihre Freigabe", level=2)
uebersetzung = {
    "booking": "Verbuchung",
    "export": "Datenexport",
    "erp_write": "Schreibender Zugriff auf ein ERP-System",
    "payment": "Zahlung",
    "filing": "Meldung oder Abgabe an eine Behoerde",
    "masterdata": "Aenderung von Stammdaten",
}
tabelle_mit(
    ["Vorgang", "Bedeutung"],
    [[uebersetzung.get(v, v), v] for v in profil["requires_approval"]],
    breiten=[7.0, 6.0],
)

kasten(
    "Der Grundsatz",
    profil["disclaimer"] + "\n\n"
    "Angebundene Fremdsysteme werden ausserdem grundsaetzlich nur gelesen, "
    "nie beschrieben - es sei denn, Sie geben das ausdruecklich frei.",
)

# ================================================================ 11
doc.add_heading("14.  Wenn etwas nicht funktioniert", level=1)

tabelle_mit(
    ["Was Sie sehen", "Was zu tun ist"],
    [
        ["Doppelklick, aber nichts passiert",
         "Auf dem Datentraeger im Ordner logs die Datei startfehler.txt oeffnen. "
         "Dort steht der Grund im Klartext."],
        ["\"Der Computer wurde durch Windows geschuetzt\"",
         "Normal beim ersten Start - die Anwendung ist noch nicht signiert. "
         "Weitere Informationen, dann Trotzdem ausfuehren."],
        ["\"Kein Sprachmodell verfuegbar\"",
         "Erwartet, solange kein Modell eingerichtet ist. Der Buchhalter "
         "recherchiert weiterhin. Einrichtung: docs/MODELL_EINRICHTEN.md"],
        ["Das Fenster geht nicht auf, Sie brauchen eine Ausgabe",
         "PORTABLE_BUCHHALTER_KONSOLE.exe verwenden - dieselbe Anwendung, aber "
         "mit Textausgabe. Zum Pruefen: PORTABLE_BUCHHALTER_KONSOLE.exe check"],
        ["Nach einem Update stimmt etwas nicht",
         "Registerkarte Wissen aktualisieren, dann Letzten Lauf zuruecknehmen."],
        ["Antwort ohne brauchbare Quellen",
         "Der Antwort nicht folgen. Frage praeziser stellen oder einen "
         "passenden Beleg hinzufuegen."],
    ],
    breiten=[6.0, 9.0],
)

doc.add_heading("Weitere Unterlagen auf dem Datentraeger", level=2)
tabelle_mit(
    ["Datei", "Inhalt"],
    [
        ["START_HIER.md", "Kurzeinstieg"],
        ["docs/MODELL_EINRICHTEN.md", "Sprachmodell einrichten"],
        ["docs/ABNAHME.md", "Abnahme Schritt fuer Schritt"],
        ["BACKUP_WIEDERHERSTELLUNG.md", "Sicherung und Wiederherstellung"],
        ["SICHERHEITSKONZEPT.md", "Wie mit Ihren Daten umgegangen wird"],
        ["TESTBERICHT.md", "Was geprueft wurde - und was nicht"],
    ],
    breiten=[6.0, 9.0],
)

doc.add_paragraph()
schluss = doc.add_paragraph()
schluss.alignment = WD_ALIGN_PARAGRAPH.CENTER
lauf = schluss.add_run(
    "Diese Anleitung beschreibt Programmfassung "
    f"{profil['version']}. Aendert sich die Oberflaeche, aendert sich auch "
    "dieses Dokument."
)
lauf.italic = True
lauf.font.size = Pt(9)
lauf.font.color.rgb = GRAU

ziel = REPO / "docs" / "BEDIENUNGSANLEITUNG.docx"
doc.save(str(ziel))


def zoom_reparieren(datei: Path) -> bool:
    """Behebt einen Schemafehler der python-docx-Vorlage.

    Deren word/settings.xml enthaelt <w:zoom w:val="none"/> ohne das laut
    OOXML-Schema vorgeschriebene Attribut w:percent. Word ist nachsichtig
    und oeffnet die Datei trotzdem; LibreOffice und andere Leseprogramme
    weisen sie ab ("source file could not be loaded"). Deshalb wird das
    Attribut hier nachgetragen.
    """
    import re
    import shutil
    import tempfile
    import zipfile

    with zipfile.ZipFile(datei) as archiv:
        inhalte = {name: archiv.read(name) for name in archiv.namelist()}

    settings = inhalte.get("word/settings.xml")
    if settings is None:
        return False
    text = settings.decode("utf-8")
    if "w:zoom" not in text or 'w:percent="' in text:
        return False
    text = re.sub(r"<w:zoom(?![^>]*w:percent)([^>]*?)/>",
                  r'<w:zoom\1 w:percent="100"/>', text, count=1)
    inhalte["word/settings.xml"] = text.encode("utf-8")

    temp = Path(tempfile.mkstemp(suffix=".docx")[1])
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as archiv:
        for name, rohdaten in inhalte.items():
            archiv.writestr(name, rohdaten)
    shutil.move(str(temp), str(datei))
    return True


if zoom_reparieren(ziel):
    print("Schemafehler der Vorlage behoben (w:zoom ohne w:percent)")
print("geschrieben:", ziel, ziel.stat().st_size, "Bytes")
