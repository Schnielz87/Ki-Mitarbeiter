# Plugin- und Erweiterungssystem

Umsetzung der Erweiterung **E5** (Abschnitte 98 bis 123 des Masterprompts).
Dieses Dokument sagt, was gebaut ist, wie es gedacht ist - und was
ausdruecklich **noch nicht** gebaut ist.

Stand siehe `PROJEKTSTATUS.md`.

---

## 1. Wozu

Ein Plugin bringt der Anwendung eine neue Faehigkeit, **ohne dass der Kern
neu gebaut wird** (E5.98). Das gilt nicht nur fuer Connectoren: auch ein
zusaetzliches Ausgabeformat, eine Wissensquelle oder ein wiederkehrender
Ablauf ist ein Plugin.

Der mitgelieferte Beispielfall in `examples/plugin_html/` zeigt das am
kleinsten sinnvollen Beispiel: er ergaenzt das Ausgabeformat HTML. Nach dem
Aktivieren steht `html` in der Formatauswahl - ohne Aenderung am Programm.

## 2. Das Paket

Ein Plugin wird als **`.kimplug`** ausgeliefert: ein ZIP-Archiv mit

```
manifest.json      Selbstbeschreibung, enthaelt die Pruefsummen aller Dateien
manifest.sig       Signatur des Herausgebers (optional)
plugin.py          der Code
```

Signiert wird das **Manifest**. Weil die SHA-256-Pruefsummen aller Dateien
im Manifest stehen, ist der Code damit mitsigniert: eine ausgetauschte Datei
faellt auf, auch wenn die Signatur selbst gueltig waere. Dateien, die nicht
im Manifest stehen, werden abgelehnt - sonst liesse sich unsignierter Code
mitschmuggeln.

Angenommen werden nur die Endungen `.py .json .md .txt .csv .html .css`.
Ein Plugin bringt Python mit, keine ausfuehrbaren Dateien und keine
Bibliotheken. Pfade, die aus dem Paketordner herausfuehren, werden
zurueckgewiesen.

Erstellt wird ein Paket mit:

```
python tools/plugin_packen.py <ordner> --ziel dist/<name> [--schluessel privat.pem]
```

Der private Schluessel des Herausgebers gehoert **nie** in die
Kundenanwendung (Masterprompt 86). In der Anwendung liegt nur der
oeffentliche Pruefschluessel.

## 3. Das Manifest

| Feld | Bedeutung |
|---|---|
| `id` | Kennung, klein geschrieben, wird zum Ordnernamen |
| `name`, `version`, `autor`, `lizenz`, `beschreibung` | Anzeige |
| `api` | Fassung der Schnittstelle, gegen die gebaut wurde (E5.110) |
| `kategorie` | CONNECTOR, KNOWLEDGE, AUTOMATION, FILE_HANDLER, MODEL, UI (E5.104) |
| `einstieg` | `modul:funktion`, wird beim Laden aufgerufen |
| `berechtigungen` | was das Plugin verlangt (E5.106) |
| `benoetigt_netz` | braucht es eine Verbindung? (E5.105) |
| `benoetigt_plugins` | Voraussetzungen (E5.111) |
| `dateien` | Datei -> SHA-256 |

Passt die Schnittstellenfassung nicht, wird das Plugin **nicht** geladen.

## 4. Berechtigungen

Jede Berechtigung wird einzeln verlangt, einzeln angezeigt und einzeln
erteilt. Was nicht erteilt wurde, gibt der Kontext nicht heraus - der
Versuch endet mit `BerechtigungFehlt` und steht im Protokoll.

```
COMPANY_MEMORY_READ / _WRITE   Unternehmensgedaechtnis
KNOWLEDGE_READ / _WRITE        Fachwissen
DATABASE_READ / _WRITE         Datenbank
FILE_READ / _WRITE             Dateien im Kundenbereich
CALENDAR_READ / _WRITE         Kalender
NETWORK_ACCESS                 Internet oder Firmennetz
MICROPHONE_ACCESS              Mikrofon
```

Schreibende Rechte und Netzzugriff sind als **schwerwiegend** markiert; die
Oberflaeche hebt sie hervor.

Zwei Sperren wirken zusammen: die Berechtigung **und** der Betriebsmodus.
Im Modus OFFLINE greift auch ein Plugin mit `NETWORK_ACCESS` nicht ins Netz
(E5.105, E2).

## 5. Ablauf einer Installation (E5.123)

```
PAKET PRUEFEN -> BERECHTIGUNGEN ZEIGEN -> BENUTZER BESTAETIGT
-> INSTALLIEREN -> AKTIVIEREN -> NEUE FAEHIGKEIT
```

Ohne Bestaetigung wird nichts installiert. Installiert ist noch nicht
aktiv: das Aktivieren ist ein zweiter, bewusster Schritt.

Auf der Kommandozeile:

```
plugin pruefen <paket.kimplug>
plugin installieren <paket.kimplug> --bestaetigen [--aktivieren]
plugin liste
plugin deaktivieren <kennung>
plugin entfernen <kennung> [--daten-loeschen]
```

## 6. Ablage und Kundentrennung (E5.120)

* **Code**: `plugins/<kennung>/` in der Wurzel der Installation. Fuer alle
  Kundenbereiche derselbe.
* **Daten**: `workspace/plugins/<kennung>/` - und `workspace` liegt im
  Kundenbereich. Ein Plugin im Bereich von Kunde A sieht die Daten von
  Kunde B nicht (Masterprompt 61).
* **Aktivierung und erteilte Rechte** gelten je Installation und stehen im
  Plugin-Ordner; die Daten bleiben beim Entfernen erhalten, sofern nicht
  ausdruecklich anderes verlangt wird (E5.113).

## 6a. Der Vorgang je Plugin

Beim Aktivieren startet die Anwendung fuer das Plugin einen eigenen
Vorgang. Sein Arbeitsverzeichnis ist der Pluginordner, seine Umgebung
traegt ``KIM_PLUGIN`` mit der Kennung - so ist im Taskmanager und im
Protokoll erkennbar, wozu er gehoert.

Beendet wird er, wenn das Plugin deaktiviert oder entfernt wird und beim
Beenden der Anwendung. Stuerzt er ab, meldet die Anwendung das beim
naechsten Aufruf des Plugins; sie selbst laeuft weiter.

## 7. Protokoll (E5.118)

Installieren, Aktivieren, Deaktivieren, Entfernen, Laden, Ladefehler,
Netzabrufe und schreibende Zugriffe auf das Gedaechtnis stehen im
Audit-Protokoll - mit Plugin-Kennung.

## 8. Fehlerverhalten

Ein Plugin darf den Start nicht verhindern. Schlaegt das Laden fehl,
schaltet sich das Plugin selbst ab, der Grund wird protokolliert und in der
Systempruefung angezeigt. Die Anwendung laeuft weiter.

---

## 9. Offen - und warum

### 9.1 Trennung auf Prozessebene (E5.108)

**Umgesetzt** - mit einer klar benannten Grenze.

Jedes Plugin laeuft in einem **eigenen Vorgang**. Die Anwendung startet ihn
und redet mit ihm ueber Standardein- und -ausgabe, je Nachricht eine Zeile
JSON. In der gepackten Fassung ruft sich das Programm dafuer selbst mit dem
Schalter ``--plugin-worker`` auf; ein python.exe daneben gibt es dort nicht.

Der Plugin-Vorgang hat **keine Datenbankverbindung, keinen Tresor und kein
Objekt der Anwendung**. Er kann nur fragen; entschieden wird im
Hauptvorgang. Die Berechtigungspruefung ist damit nicht mehr eine Absprache
unter Gleichen, sondern die einzige Tuer zu den Daten.

Angemeldete Faehigkeiten werden als Stellvertreter gefuehrt: der Aufruf
eines Werkzeugs reist hinueber, ein Ausgabeformat wird drueben erzeugt und
kommt als Bytes zurueck.

**Was das nicht leistet:** der Vorgang laeuft mit denselben Benutzerrechten
wie die Anwendung. Er koennte Dateien oeffnen, die dem angemeldeten
Benutzer gehoeren, oder selbst eine Verbindung aufbauen. Eine Beschraenkung
durch das Betriebssystem - eigenes Benutzerkonto, Job-Objekt unter Windows,
seccomp unter Linux - ist **nicht** eingerichtet. Wer Plugins voellig
fremder Herkunft zulassen will, braucht diesen Schritt zusaetzlich.

Deshalb gelten die drei uebrigen Vorkehrungen unveraendert weiter:

1. nur signierte Pakete gelten als vertrauenswuerdig,
2. jede Berechtigung wird einzeln erteilt und protokolliert,
3. der Benutzer sieht vor der Installation, was verlangt wird.

Geprueft wird die Trennung mit einem absichtlich neugierigen Testplugin:
andere Vorgangskennung, keine Objekte der Anwendung sichtbar, ohne Recht
kein Wert ueber die Leitung, vom Pluginordner aus keine Datenbank
erreichbar, und ein abstuerzender Vorgang reisst die Anwendung nicht mit.

### 9.2 Pruefschluessel des Herausgebers (E5.109)

In dieser Fassung ist **kein** Herausgeberschluessel hinterlegt - dieselbe
Lage wie bei der Lizenz (Masterprompt 86). Solange keiner hinterlegt ist,
kann eine vorhandene Signatur nicht geprueft werden; die Anwendung sagt das,
statt Gueltigkeit vorzutaeuschen.

### 9.3 Plugin-Katalog (E5.116)

**Nicht umgesetzt.** Ein Katalog setzt einen Betreiber, eine Adresse und
eine Pruefstelle voraus - eine geschaeftliche Entscheidung. Die Installation
aus einer lokalen Datei (E5.117) ist umgesetzt und deckt den portablen
Betrieb ab.

### 9.4 Plugin-Lizenzierung (E5.119)

**Nicht umgesetzt.** Die Lizenzarchitektur traegt es (die Lizenz kennt
Module), aber welche Plugins kostenpflichtig sind, ist eine
Geschaeftsentscheidung. Vgl. Masterprompt 78: das Geschaeftsmodell wird
nicht fest in die Technik gebaut.

### 9.5 Automatische Plugin-Updates (E5.112)

**Teilweise.** Eine erneute Installation ersetzt die vorhandene Fassung
sauber. Ein Abgleich gegen eine Bezugsquelle setzt den Katalog voraus.

### 9.6 Aufloesung von Abhaengigkeiten (E5.111)

**Teilweise.** Vorausgesetzte Plugins muessen vorhanden sein, sonst wird
abgelehnt. Eine Aufloesung von Fassungen und eine Reihenfolge beim Laden
gibt es noch nicht.

---

## 10. Commercial-Ready-Gate fuer Plugins (E5.122)

Nach E5.122 darf der Status COMMERCIAL READY fuer Plugins Dritter nicht
vergeben werden, solange Sandboxing, Signaturpruefung mit hinterlegtem
Schluessel und der Katalogprozess nicht stehen.

Stand jetzt:

| Voraussetzung | Lage |
|---|---|
| Trennung der Vorgaenge | **steht** (9.1) |
| Beschraenkung durch das Betriebssystem | offen (9.1) |
| Signaturpruefung | gebaut und geprueft; **Herausgeberschluessel fehlt** (9.2) |
| Katalogprozess | offen (9.3) |

Fuer eigene, mit dem Produkt ausgelieferte Plugins ist der Stand tragfaehig.
Fuer Plugins voellig fremder Herkunft ist er es nicht - dafuer fehlen die
beiden offenen Punkte.
