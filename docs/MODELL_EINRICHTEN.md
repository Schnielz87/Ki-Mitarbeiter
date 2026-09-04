# Sprachmodell einrichten

Ohne lokales Sprachmodell recherchiert der Buchhalter zwar in seinen Quellen
und zeigt die Fundstellen an, **formuliert aber keine Fachantwort**. Er sagt
das dann auch deutlich. Diese Anleitung schliesst die Luecke.

Einmaliger Aufwand: etwa 15 Minuten plus Downloadzeit.

## Schritt 1: Passendes Modell ermitteln

```
PORTABLE_BUCHHALTER.exe                       (oder: python portable_buchhalter.py)
python tools\modell_einrichten.py empfehlen
```

Die Ausgabe nennt Prozessor, Arbeitsspeicher, Grafikkarte und freien Platz
und empfiehlt ein Profil:

| Profil | Modellklasse | Bedarf | Einschaetzung |
|---|---|---|---|
| LIGHT | 3B, Q4_K_M, etwa 2 GB | ab 6 GB RAM | Laeuft ueberall. Fachqualitaet begrenzt - Antworten besonders sorgfaeltig pruefen. |
| STANDARD | 7-8B, Q4_K_M, etwa 5 GB | ab 12 GB RAM | **Empfehlung.** Gute deutsche Sprachqualitaet bei vertretbarem Bedarf. |
| HIGH QUALITY | 12-14B, Q5_K_M, etwa 9 GB | ab 24 GB RAM | Beste Qualitaet. Auf reiner CPU spuerbar langsamer. |

Empfohlene Modelle (alle mit freier Lizenz, Apache 2.0):

* **LIGHT**: Qwen2.5-3B-Instruct, Quantisierung Q4_K_M
* **STANDARD**: Qwen2.5-7B-Instruct, Quantisierung Q4_K_M
* **HIGH QUALITY**: Mistral-Nemo-Instruct-2407 (Q5_K_M) oder
  Qwen2.5-14B-Instruct (Q4_K_M)

Wichtig ist das Dateiformat **GGUF**. Andere Formate (safetensors, GPTQ, AWQ)
funktionieren mit llama.cpp nicht.

## Schritt 2: Modell beschaffen

Die GGUF-Datei nach `models\` legen. Zwei Wege:

**Von Hand:** Datei herunterladen (ueblicherweise von Hugging Face) und in
den Ordner `models\` kopieren. Fertig.

**Mit dem Werkzeug:**

```
python tools\modell_einrichten.py laden <URL> --sha256 <pruefsumme>
```

Die Pruefsumme ist optional, aber empfohlen: ohne sie ist die Datei nicht
gegen Manipulation geprueft. Das Werkzeug bricht bei falscher Pruefsumme ab
und verwirft die Datei.

Bitte die Lizenz des jeweiligen Modells beachten. Fuer den geschaeftlichen
Einsatz sind Apache-2.0-Modelle unproblematisch.

## Schritt 3: Ausfuehrungsweg waehlen

Zwei Wege - der zweite ist fuer den portablen Betrieb meist der bessere.

### Weg A: im selben Prozess (`llama-cpp-python`)

```
python -m pip install llama-cpp-python
```

Vorteil: nichts weiter zu starten.
Nachteil: das Paket muss auf manchen Rechnern kompiliert werden, was einen
C-Compiler verlangt. Deshalb ist es **keine** Pflichtabhaengigkeit.

### Weg B: llama-server aus llama.cpp (empfohlen)

1. Die vorkompilierten Windows-Dateien von llama.cpp herunterladen und nach
   `runtime\llama\` entpacken.
2. Server starten:

```
runtime\llama\llama-server.exe -m models\<modell>.gguf -c 8192 --port 8080
```

3. In `config\settings.json` eintragen:

```json
{ "llm": { "server_url": "http://127.0.0.1:8080", "server_model": "local" } }
```

Vorteile: keine Kompilierung, klare Trennung, das Modell bleibt zwischen den
Starts geladen, GPU-Unterstuetzung ueber die Startparameter von llama.cpp.
Der Server laeuft ausschliesslich auf `127.0.0.1` - es ist **kein** Server im
Sinne des Masterprompts, sondern ein lokaler Hilfsprozess ohne Netzzugang.

## Schritt 4: Wirklich pruefen

```
python tools\modell_einrichten.py pruefen
```

oder fuer Weg B:

```
python tools\modell_einrichten.py pruefen --server http://127.0.0.1:8080
```

Das Werkzeug stellt eine echte Testfrage und zeigt Antwort, Dauer und
Geschwindigkeit. Erst wenn hier eine sinnvolle Antwort steht, ist das Modell
eingerichtet.

Anschliessend:

```
PORTABLE_BUCHHALTER.exe check
```

Die Zeile „Lokales Modell" muss **OK** zeigen, nicht **HINWEIS**.

## Einstellungen

In `config\settings.json` unter `llm`:

| Schluessel | Bedeutung |
|---|---|
| `model_path` | `"auto"` waehlt die groesste GGUF-Datei in `models\`, sonst ein konkreter Pfad |
| `context_tokens` | Kontextfenster, Vorgabe 8192 |
| `max_output_tokens` | Laenge der Antwort, Vorgabe 1024 |
| `temperature` | Vorgabe 0.2 - fuer Fachfragen bewusst niedrig |
| `threads` | 0 bedeutet automatisch |
| `gpu_layers` | 0 bedeutet reine CPU; hoeher setzen, wenn eine Grafikkarte vorhanden ist |
| `server_url` | gesetzt = Weg B wird verwendet |

## Wenn es nicht klappt

| Beobachtung | Ursache und Abhilfe |
|---|---|
| „kein GGUF-Modell in ..." | Datei liegt nicht in `models\` oder hat nicht die Endung `.gguf` |
| „llama-cpp-python ist nicht installiert" | Weg B verwenden - er braucht kein Python-Paket |
| „Modelldienst nicht erreichbar" | `llama-server.exe` laeuft nicht oder nutzt einen anderen Port |
| Antworten sehr langsam | kleineres Profil waehlen oder `gpu_layers` erhoehen |
| Antworten sprachlich schwach | groesseres Modell verwenden; 3B-Modelle sind fuer Fachtexte grenzwertig |
| Speicher voll | staerker quantisierte Fassung nehmen (Q4 statt Q5) |

## Modell wechseln

Alte Datei aus `models\` entfernen, neue hineinlegen, `check` ausfuehren.
Das Modell ist austauschbar; Wissensbasis und Unternehmensgedaechtnis bleiben
davon unberuehrt.
