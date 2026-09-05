# START HIER

## Was ist das?

Ein **portabler KI-Buchhalter**. Er liegt vollstaendig auf diesem
Datentraeger, arbeitet **ohne Internet** und merkt sich, was Sie ihm ueber Ihr
Unternehmen sagen - dauerhaft, hier auf dem Datentraeger, nicht auf dem
jeweiligen Rechner.

## In drei Schritten loslegen

1. Datentraeger an einen Windows-PC anschliessen.
2. Diesen Ordner oeffnen.
3. **PORTABLE_BUCHHALTER.exe** doppelklicken.

Es oeffnet sich ein Fenster mit einer Systempruefung. Wenn dort
„Der Buchhalter kann gestartet werden" steht, auf **BUCHHALTER STARTEN**
klicken.

> **Liegt hier noch keine `PORTABLE_BUCHHALTER.exe`?** Dann wurde sie fuer
> diesen Datentraeger noch nicht aufgespielt. Das fertige Paket gibt es
> gebaut zum Herunterladen:
>
> 1. **Bei GitHub anmelden.** Das ist zwingend: GitHub liefert Artefakte nur
>    an angemeldete Nutzer aus. Nicht angemeldet sehen Sie den Kasten zwar,
>    der Name ist dann aber **kein Link** - ein Klick tut schlicht nichts.
>    Oben rechts pruefen: steht dort Ihr Profilbild oder *Sign in*?
> 2. https://github.com/Schnielz87/Ki-Mitarbeiter/actions oeffnen und den
>    **obersten Ablauf mit gruenem Haken** anklicken. Dort steht immer die
>    neueste Fassung - so brauchen Sie sich keinen Link zu merken und
>    bekommen nie eine veraltete Fassung.
> 3. Ganz unten im Kasten **Artefakte** (englisch *Artifacts*) **direkt auf
>    den Namen** `Portable-Buchhalter-Windows` klicken. Das Wort selbst ist
>    der Link; angemeldet ist es blau. Es kommt eine ZIP-Datei, GitHub zeigt
>    die Groesse als **21,9 MB** an.
> 4. ZIP **auf den Datentraeger entpacken**, nicht in den Download-Ordner.
>    Windows blockiert sonst unter Umstaenden die Ausfuehrung.
> 5. Rechtsklick auf die ZIP-Datei vor dem Entpacken → *Eigenschaften* →
>    falls dort **Zulassen** oder *Entsperren* steht, anhaken. Das ist die
>    uebliche Windows-Sperre fuer heruntergeladene Dateien.
> 6. Danach `PORTABLE_BUCHHALTER.exe` doppelklicken.
>
> Die Anwendung ist **nicht signiert** (Code-Signing steht noch aus). Windows
> SmartScreen meldet sich deshalb beim ersten Start mit
> *"Der Computer wurde durch Windows geschuetzt"*. Dort auf
> **Weitere Informationen** → **Trotzdem ausfuehren**.
>
> Alternativ selbst bauen nach `docs/ABNAHME.md`, oder zum blossen
> Ausprobieren `PORTABLE_BUCHHALTER.bat` - dafuer braucht der PC allerdings
> eine Python-Installation.

## Ausfuehrliche Bedienungsanleitung

`docs\BEDIENUNGSANLEITUNG.docx` - als Word-Dokument, elf Kapitel: wo Sie was
eingeben, wie eine Antwort aufgebaut ist, was der Buchhalter bewusst nicht
tut, und was zu tun ist, wenn etwas nicht funktioniert.

## Was Sie **nicht** brauchen

Kein Python, kein Git, keine Entwicklungsumgebung, keinen Compiler, kein
Terminal, keine Administratorrechte, keine Installation - und keinen Server.

## Was Sie einmalig einrichten sollten

### 1. Sprachmodell (einmalig, etwa 5 GB)

Ohne Sprachmodell recherchiert die Anwendung zwar in ihren Quellen, kann aber
**keine ausformulierte Fachantwort** geben. Sie sagt das dann auch deutlich.

Anleitung: `docs/MODELL_EINRICHTEN.md`

### 2. Angaben zu Ihrem Unternehmen

In der Anwendung: Registerkarte **Unternehmenswissen** →
**Onboarding fortsetzen**. Dort werden Kontenrahmen, Rechtsform,
Freigaberegeln und Aehnliches abgefragt. Alles davon darf leer bleiben und
spaeter ergaenzt werden.

Sie koennen solche Angaben auch einfach im Gespraech sagen, zum Beispiel:

> „Wir verwenden grundsaetzlich SKR03."

Der Buchhalter fragt dann nach, ob er sich das dauerhaft merken soll.

### 3. Fachwissen aktualisieren (nur mit Internet)

Registerkarte **Wissen aktualisieren** → **Wissen jetzt aktualisieren**.
Die geladenen Texte werden lokal gespeichert und stehen danach **auch ohne
Internet** zur Verfuegung.

## Was der Buchhalter kann

Sachverhalte einordnen, Kontierungs- und Buchungsvorschlaege erstellen,
Rechnungen auf Pflichtangaben pruefen, Umsatzsteuerfragen aufbereiten
(Vorsteuer, Reverse Charge, innergemeinschaftliche Vorgaenge, Leistungsort),
Anlagevermoegen und Abschreibungen, Abgrenzungen und Rueckstellungen, GoBD
und Aufbewahrung, Jahresabschlussvorbereitung, Belege auswerten, Berechnungen
und Quellenrecherche.

## Was er ausdruecklich **nicht** ist

Er ersetzt **nicht** den Steuerberater, den Wirtschaftspruefer, den
verantwortlichen Buchhalter oder die Geschaeftsfuehrung. Er leistet Zuarbeit.
Buchungen, Meldungen und Zahlungen brauchen immer die Pruefung und Freigabe
eines Menschen.

Wenn er sich nicht sicher ist, sagt er das - er raet nicht.

## Datentraeger an einen anderen PC

Einfach abziehen und am anderen Rechner anstecken. Alles wandert mit: das
Unternehmenswissen, die Gespraeche, die Belege, die Einstellungen, das
Fachwissen. Auch ein anderer Laufwerksbuchstabe (D:, E:, F: ...) ist kein
Problem.

## Wenn etwas nicht geht

| Beobachtung | Was zu tun ist |
|---|---|
| Die EXE startet nicht | `PORTABLE_BUCHHALTER_KONSOLE.exe check` in der Eingabeaufforderung ausfuehren - die Ausgabe nennt den Grund |
| „Kein Sprachmodell verfuegbar" | `docs/MODELL_EINRICHTEN.md` |
| Antworten ohne Quellen | Registerkarte **Wissen aktualisieren** ausfuehren (braucht Internet) |
| Der Datentraeger ist voll | Alte Ordner unter `updates\` und `backups\` loeschen |
| Etwas ging verloren | `BACKUP_WIEDERHERSTELLUNG.md` |

## Die beiden Programme

| Datei | Wofuer |
|---|---|
| `PORTABLE_BUCHHALTER.exe` | **Das normale Programm.** Doppelklick genuegt. |
| `PORTABLE_BUCHHALTER_KONSOLE.exe` | Nur fuer die Eingabeaufforderung, etwa zur Fehlersuche. Beide enthalten denselben Buchhalter. |

## Wichtige Dateien in diesem Ordner

| Datei / Ordner | Inhalt |
|---|---|
| `README.md` | Ausfuehrliche Beschreibung |
| `docs/ABNAHME.md` | Schritt-fuer-Schritt-Pruefung, ob alles funktioniert |
| `docs/MODELL_EINRICHTEN.md` | Sprachmodell einrichten |
| `SICHERHEITSKONZEPT.md` | Datenschutz und Verlust des Datentraegers |
| `BACKUP_WIEDERHERSTELLUNG.md` | Sichern und Wiederherstellen |
| `company\` | Ihr Unternehmensprofil, lesbar exportiert |
| `database\company.db` | Unternehmensgedaechtnis - **die wichtigste Datei** |
| `logs\` | Protokolle bei Problemen |

## Wenn das Artefakt sich nicht herunterladen laesst

Der haeufigste Fall: **nicht bei GitHub angemeldet**. Artefakte werden nur an
angemeldete Nutzer ausgeliefert. Der Kasten ist trotzdem zu sehen, der Name
ist aber kein Link - der Klick bleibt wirkungslos. Woran man es erkennt: die
uebrigen Verweise der Seite sind blau, der Artefaktname schwarz.

Zweiter Fall: **das Artefakt ist abgelaufen.** Artefakte werden nach 30 Tagen
geloescht. Dann einfach den neuesten Ablauf unter
https://github.com/Schnielz87/Ki-Mitarbeiter/actions nehmen - jeder
erfolgreiche Ablauf legt ein frisches Paket ab.

Das Symbol neben der Pruefsumme (`sha256:...`) ist **nicht** der Download; es
kopiert nur die Pruefsumme in die Zwischenablage.
