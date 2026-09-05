# Hier weitermachen

Diese Datei ist der Wiedereinstiegspunkt. Sie wurde geschrieben, weil die
Arbeit auf Wunsch des Auftraggebers unterbrochen wurde (Limit). Der Chat wird
zum Fortsetzen **nicht** benoetigt.

## Erledigt seit dem Wiedereinstieg (Fassung 0.2.0)

**Die Erweiterung des Masterprompts um die Abschnitte 58 bis 97 ist
umgesetzt** - kommerzielle Produktperspektive und Lizenzierung. Einzelheiten
in `ANFORDERUNGSNACHWEIS.md`, Tasks 19 bis 24 in `checkpoints/`.

Der Auftrag selbst liegt jetzt als `MASTERPROMPT.md` auf dem Datentraeger.

### Naechster Schritt

1. `docs/ABNAHME.md` Punkte B bis G auf einem Windows-Rechner - Punkt A ist
   durch den Windows-Ablauf belegt, das fertige Paket kann dort
   heruntergeladen werden.
2. `PORTABLE_BUCHHALTER_KONSOLE.exe reife` zeigt den Stand auf dem Weg zur
   kommerziellen Freigabe.
3. Danach in dieser Reihenfolge: rechtliche Pruefung (Abgrenzung zur
   Steuerberatung), Pilotkunde, externe Sicherheitspruefung, Pruefschluessel
   und Code-Signing.

## Frueherer Wiedereinstiegspunkt

Der als naechstes vorgesehene Schritt - „Baut die EXE durch?" - ist
**beantwortet: ja**. Ablauf https://github.com/Schnielz87/Ki-Mitarbeiter/actions/runs/33970160321
hat alle 13 Schritte bestanden. Dabei kamen vier echte Fehler heraus, die
alle behoben sind: Fensterprogramm ohne Ausgabe unter Windows, Schalter nur
vor dem Unterbefehl erlaubt, Ausbruch der Datei-Connectoren aus ihrem
Verzeichnis, Ausbruch ueber Kennungen des Quellenregisters. Task 17 steht
jetzt belegt auf GEBAUT.

Offen bleiben die Abnahmepunkte, die ein echtes Sprachmodell, das Oeffnen
des Fensters, einen zweiten Rechner oder die echten amtlichen Quellen
brauchen - siehe `docs/ABNAHME.md`.

## Stand

| | |
|---|---|
| Branch | `claude/portable-ki-buchhalter-xr1qlj` |
| Letzter Commit | `c740ef0` - Haertung: Chunk-Ueberlappung, Fortschritt ueber eine Warteschleife |
| Gepusht | ja |
| Tests | **116 gruen, 1 uebersprungen** (`python -m pytest tests -q`) |
| Arbeitsverzeichnis | sauber, keine offenen Aenderungen |
| Tasks 01-16 | abgeschlossen |
| Tasks 17-18 | teilweise - offen ist nur, was Windows, echte Oberflaeche, echtes Modell oder echte Quellen braucht |

Alles Weitere: `PROJEKTSTATUS.md`, `checkpoints/LETZTER_STAND.json`,
`TESTBERICHT.md`.

## Zuletzt getan (in dieser Reihenfolge)

1. Windows-Ablauf der Fortlaufenden Integration ausgewertet: **112 von 113
   Tests bestanden auf echtem Windows**. Der eine Fehlschlag lag im Test
   (Windows ignoriert POSIX-Rechtebits auf Verzeichnissen), nicht in der
   Anwendung. Behoben, zwei plattformunabhaengige Tests ergaenzt.
2. Selbstpruefung: Pfadzugriff vereinheitlicht, Binaerdaten koennen nicht
   mehr als Fachwissen in den Index geraten, Chunk-Ueberlappung begrenzt,
   Fortschrittsanzeige der Oberflaeche threadsicher gemacht.

## Als Naechstes - genau hier ansetzen

### 1. Ergebnis des Windows-Ablaufs pruefen (wichtigster Punkt)

Der Push von `c740ef0` hat einen neuen Lauf ausgeloest. Beim letzten Lauf
scheiterte der Windows-Job noch an dem inzwischen behobenen Test, weshalb
**der EXE-Bau bisher nie ausgefuehrt wurde** (die Schritte 7 bis 13 waren
uebersprungen).

Zu pruefen:

* Laeuft der Job `EXE bauen und pruefen (Windows)` jetzt durch?
* Entsteht `PORTABLE_BUCHHALTER.exe` tatsaechlich?
* Bestehen die Schritte: Systempruefung der EXE, Offline-Fachfrage mit
  Quellenteil, dauerhaftes Speichern von Unternehmenswissen, Laufwerkswechsel
  ueber `subst` mit Leerzeichen im Pfad?

Ablaufuebersicht:
`https://github.com/Schnielz87/Ki-Mitarbeiter/actions`

Erst wenn das gruen ist, darf in `PROJEKTSTATUS.md` bei Task 17 aus
"EXE nicht gebaut" ein **GEBAUT** werden - und zwar mit Verweis auf den
konkreten Lauf. Vorher nicht (Masterprompt 52).

Zu erwartende Stolpersteine im PowerShell-Skript, falls es scheitert:

* `Copy-Item "$Ausgabe\*"` bei leerem Zielordner
* Pfade mit Leerzeichen in `build_windows.ps1`
* PyInstaller findet ein verstecktes Modul nicht - dann in
  `build/portable_buchhalter.spec` unter `hidden_imports` ergaenzen
* Tkinter-Bestandteile fehlen im Build - dann PyInstaller-Hooks pruefen

### 2. Danach, in dieser Reihenfolge

1. **Ergebnis eintragen**: `PROJEKTSTATUS.md` Task 17/18 und `TESTBERICHT.md`
   auf den dann tatsaechlichen Stand bringen; Checkpoint 17 und 18 neu
   schreiben (`python tools/checkpoint.py create ...`).
2. **Artefakt sichern**: Der Ablauf legt den fertigen portablen Ordner als
   Artefakt ab. Im Abnahmedokument darauf verweisen, damit der Auftraggeber
   ihn herunterladen kann, ohne selbst zu bauen.
3. **Offene Punkte aus `docs/ABNAHME.md`** bleiben beim Auftraggeber:
   echtes Sprachmodell (C), fachliche Beurteilung der Antworten (D),
   zweiter PC (F), Validierung der Quellen-URLs (G).

### 3. Sinnvolle Ausbaustufen danach

* Auswahl mehrerer Mitarbeiter beim Start (Masterprompt 54)
* DATEV-Format als erster echter ERP-Weg - kommt ohne Zugaenge und VPN aus
* Mitgelieferte Python-Laufzeit, damit auch der Startweg ohne EXE kein
  installiertes Python braucht

## Was bewusst NICHT behauptet wird

Der Status lautet **nicht** "MVP FERTIG", sondern **"fertig zur Abnahme"**.
Nicht ausgefuehrt wurden: der EXE-Bau in dieser Umgebung, die echte
Tkinter-Oberflaeche, ein echtes Sprachmodell, der Abruf der echten amtlichen
Quellen, ein echter zweiter PC. Begruendung und Abnahmeweg stehen in
`PROJEKTSTATUS.md` Abschnitt 5 und in `docs/ABNAHME.md`.

## Umgebungshinweise fuer die naechste Sitzung

* Entwicklungsumgebung ist Linux **ohne Tkinter und ohne Bildschirm** - die
  Oberflaeche laesst sich dort nicht ausfuehren, nur ueber das Doppel in
  `tests/tk_double.py` pruefen.
* Der Netzzugang ist auf Paketregistries beschraenkt; amtliche Hosts
  antworten mit 403 des Proxys. Netzcode wird deshalb gegen lokale
  Testserver geprueft.
* Testabhaengigkeiten nachinstallieren:
  `pip install --break-system-packages pytest cryptography pypdf cffi`
* Checkpoints ausserhalb des Repositorys:
  `KIM_CHECKPOINT_DIR=/home/user/ki-agent-checkpoints` setzen (in diesem
  Container fluechtig; unter Windows ist `D:\Ki-Agent\checkpoints` die
  Vorgabe).
