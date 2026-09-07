# PORTIVA — UI/UX-Konzept

Stand **2026-09-07**. Grundlage: verbindlicher UI/UX-Auftrag,
Referenzbilder 00–10 (`docs/UI_Referenzen/`), PORTIVA-Classic-Logo.

Dieses Dokument beschreibt, **was gebaut wurde und warum**. Was noch
fehlt, steht in Abschnitt 7 — ausdrücklich und ohne Beschönigung.

---

## 1. Aufbau

    ┌──────────────┬───────────────────────────────────────────┐
    │              │  Titel der Ansicht      [Chips: Stand,    │
    │  PORTIVA     │  Untertitel              Modus, Internet] │
    │  (Logo)      ├───────────────────────────────────────────┤
    │              │                                           │
    │  ▸ 10 Berei- │   Inhalt der aktiven Ansicht              │
    │    che, der  │                                           │
    │    aktive    │   (in der Unterhaltung zusätzlich rechts   │
    │    hervor-   │    das einklappbare Quellenpanel)         │
    │    gehoben   │                                           │
    │              ├───────────────────────────────────────────┤
    │  Profil      │  Statuszeile                              │
    │  Lage        │                                           │
    └──────────────┴───────────────────────────────────────────┘

Drei Module tragen den Rahmen:

| Modul | Aufgabe |
|---|---|
| `src/ui/startbild.py` | Begrüßungsbild, 3 Sekunden |
| `src/ui/schale.py` | Seitenleiste, Kopfzeile, Bühne für die Ansichten |
| `src/ui/quellenpanel.py` | Quellenkarten und Recherche-Details |

Die Schale kennt **keine Fachlogik**. Sie nimmt eine Fläche entgegen und
zeigt sie an; sie weiß nichts über Unterhaltung, Belege oder
Einstellungen. Was sie nicht kennt, kann sie auch nicht kaputtmachen.

## 2. Die zehn Bereiche

Reihenfolge und Benennung folgen dem Zielentwurf. Ein Test hält beides
fest — elf wären einer zu viel, neun einer zu wenig.

1. Unterhaltung · 2. Unternehmenswissen · 3. Belege & Dokumente ·
4. Arbeitsergebnisse · 5. Wissen & Quellen · 6. Vorlagen · 7. Aufgaben ·
8. Plugins · 9. Verbundene Dienste · 10. Einstellungen & Status

Das Sprachmodell ist **kein** eigener Bereich, sondern die Gruppe
„KI & Modelle" unter Einstellungen. Es ist eine Einstellung, kein
Arbeitsbereich.

Die Navigation ist profilspezifisch: steht im Profil eine Liste
`navigation`, erscheinen nur diese Bereiche. Ausgeblendet heißt dabei
nicht gelöscht — die Fläche wird trotzdem gebaut, damit der Code einer
Ansicht für jedes Profil derselbe bleibt.

## 3. Entscheidungen, die Begründung brauchen

### Einfache tk-Bausteine in der Seitenleiste
ttk färbt sich je nach System unterschiedlich, und ein dunkler Hintergrund
lässt sich dort unter Windows nicht verbindlich durchsetzen. Die
Seitenleiste soll auf jedem Rechner gleich aussehen.

### Drag & Drop über die Windows-Systemschnittstelle
Statt einer zusätzlichen Bibliothek (`tkinterdnd2`) meldet sich das
Fenster mit `DragAcceptFiles` an und fängt `WM_DROPFILES` ab. Grund: das
Paket läuft von einem Datenträger an fremden Rechnern, und jede weitere
Binärdatei darin ist eine weitere Fehlerquelle.

Klappt es nicht, bleibt die Ablagefläche ein Klickziel **und sagt das
auch**. Eine Aufforderung zum Ziehen, die nicht funktioniert, wäre
schlimmer als keine.

### Technisches getrennt vom Fachlichen
Bewertungen, Dokument-Kennungen und die Zahlen „gefunden / verwendet"
stehen ausschließlich unter „Recherche-Details", standardmäßig
geschlossen. Eine Bewertungszahl neben einer Gesetzesangabe sieht aus, als
gehöre sie zur fachlichen Aussage. Sie tut es nicht.

### Leere Felder werden weggelassen
Ein Feld, das bei jeder Quelle „unbekannt" sagt, ist Lärm. Angezeigt wird
nur, was es wirklich gibt.

### Leerezustände sagen, was los ist
„Noch keine Plugins installiert", „kein auswertbarer Text", „Zu dieser
Frage wurde keine Fundstelle herangezogen". Ein Gedankenstrich lässt
offen, ob nichts gefunden wurde oder ob gar nichts passiert ist.

### Zurückhaltende Ampeln
Im Systemstatus bekommt nur Farbe, was eindeutig gut oder eindeutig
fehlerhaft ist. Eine grüne Ampel, die nichts bedeutet, ist schlimmer als
gar keine.

## 4. Tastenbelegung

| Taste | Wirkung |
|---|---|
| Eingabe | Nachricht senden |
| Umschalt + Eingabe | Zeilenumbruch |
| Strg + N | Neue Unterhaltung |
| Escape | Laufende Antwort abbrechen (tut nichts, wenn nichts läuft) |

Vorher war es Strg+Eingabe — das kennt aus anderen Anwendungen niemand.

## 5. Keine toten Knöpfe

Auftrag Abschnitt 34 lässt zwei Möglichkeiten: eine Aktion funktioniert,
oder sie ist eindeutig als nicht verfügbar gekennzeichnet.

- **62 Bedienelemente, 0 ohne Rückruf** — nachgewiesen in
  `UI_BUTTON_FUNKTIONSMATRIX.md`, erzeugt aus dem laufenden Fenster.
- Ein Test (`tests/test_keine_toten_knoepfe.py`) läuft über alle zehn
  Bereiche. Er findet auch Knöpfe **ohne** Rückruf — dafür kennt das
  Testdoppel Knöpfe als eigene Art. Ohne diese Unterscheidung fand er
  ausgerechnet die nicht, um die es geht.
- Vorlagen und Aufgaben tragen den zweiten Fall: sie erklären, was sie
  können werden und was heute stattdessen hilft. Ihr einziger Knopf führt
  in einen Bereich, den es gibt.

## 6. Abweichungen von den Referenzbildern

Der Auftrag erlaubt begründete Abweichungen, wenn sie dokumentiert werden.

| Abweichung | Grund |
|---|---|
| Der Betriebsmodus ist ein Auswahlfeld, kein Chip | Er ist eine Entscheidung, kein Zustand. Ein Chip zeigt nur an; ein Auswahlfeld lässt handeln (Abschnitt 31: schnell erreichbar). |
| Die Statuszeile unten blieb erhalten | Sie nennt den Pfad des Datenträgers und während einer Frage, worauf gewartet wird. Beides steht in keinem Referenzbild und beides wurde im Betrieb gebraucht. |
| Einstellungen nutzen Gruppenreiter statt Kacheln | Kacheln, die nur zu einer Liste führen, sind ein Umweg. Die acht Gruppen sind direkt erreichbar. |
| Kein Zahlen-Sinnbild je Navigationseintrag | Ein Zeichen ist immer da, eine Bilddatei kann fehlen — und ein leerer Knopf wäre schlechter als ein schlichtes Zeichen. |

## 7. Was noch fehlt

Ehrlich und vollständig:

1. **Vorlagen und Aufgaben** — nach Entscheidung des Auftraggebers ein
   eigener Auftrag. Beide brauchen neue Fachlogik, nicht nur Oberfläche.
2. **Drag & Drop ist nicht erprobt.** In dieser Umgebung gibt es kein
   Windows und keinen Bildschirm. Der Code ist so gebaut, dass ein
   Fehlschlag folgenlos bleibt; ob das Ziehen wirklich geht, zeigt der
   Betrieb.
3. **Die echte Tkinter-Oberfläche wurde nie geöffnet.** Geprüft wird gegen
   ein Doppel. Aussehen, Layout und echtes Tk-Verhalten sind damit nicht
   geprüft.
4. **Windows-Skalierung 100/125/150 %** ist ungeprüft.
5. **Der Plugin-Katalog** (Reiter „Katalog") fehlt — installieren aus
   einer Datei geht, ein Katalog zum Stöbern nicht.

Punkte 2 bis 4 lassen sich nur auf einem echten Windows-Rechner mit
Bildschirm abnehmen. Sie stehen unverändert in `docs/ABNAHME.md`.
