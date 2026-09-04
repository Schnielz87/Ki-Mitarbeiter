# Einen weiteren KI-Mitarbeiter anlegen

Masterprompt Abschnitte 2, 53, 54.

## Was wiederverwendet wird

Alles unter `src/pkc`, `src/app` und `src/ui` ist fachneutral: Oberflaeche,
Kommandozeile, Modellverwaltung, Recherche, Wissensdatenbank,
Unternehmensgedaechtnis, Datenhaltung, Update-Engine, Sicherheit, Freigaben,
Protokoll, Connector-Rahmen, Packaging, Checkpoints.

Ein automatischer Test wuerde auffallen lassen, wenn dort
buchhaltungsspezifische Begriffe einziehen: der Core kennt „Rechnung" und
„Vorsteuer" nicht - diese Woerter stehen ausschliesslich im Profil und in
dessen Fachmodulen.

## Was ausgetauscht wird

Ein neues Verzeichnis unter `src/profiles/<rolle>/`:

```
src/profiles/controller/
    profile.json            Rolle, Faehigkeiten, Grenzen, Freigabepflichten,
                            Antwortschema, Onboarding-Schluessel
    prompts/system.md       Fach-Masterprompt der Rolle
    knowledge/*.md          mitgelieferte Fachmodule
    testcases.json          fachliche Testfaelle
    sources.json            optional: rollenspezifische Quellen
```

## Schritt fuer Schritt

### 1. Verzeichnis anlegen

Am einfachsten das Buchhalterprofil kopieren und anpassen.

### 2. `profile.json` fuellen

```json
{
  "profile_id": "controller",
  "name": "Portabler KI-Controller",
  "role": "Digitaler Fachmitarbeiter fuer Controlling (Zuarbeit)",
  "version": "0.1.0",
  "system_prompt": "prompts/system.md",
  "capabilities": ["Abweichungsanalysen", "Deckungsbeitragsrechnung", "..."],
  "limits": ["Keine Unternehmensbewertung mit Rechtswirkung", "..."],
  "requires_approval": ["export", "erp_write"],
  "answer_sections": ["ERGEBNIS", "BEGRUENDUNG", "ANNAHMEN", "..."],
  "onboarding_keys": ["company.name", "company.fiscal_year", "..."],
  "knowledge_modules": ["kostenrechnung", "kennzahlen"],
  "default_connectors": ["csv", "excel"]
}
```

### 3. Masterprompt schreiben

`prompts/system.md`. Bewaehrte Gliederung des Buchhalters:

1. Rolle und was sie ausdruecklich nicht ist
2. unumstoessliche Regeln (nichts erfinden, Fundstellen zuerst,
   Quellenhierarchie, Zeitbezug, Unternehmenskontext, keine Scheinhandlungen,
   keine verbindliche Ausfuehrung, Sprache)
3. Vorgehen bei Fachanfragen
4. Antwortschema
5. Verhalten bei Unsicherheit

Die Datei muss mindestens 200 Zeichen haben - kuerzere lehnt der Lader mit
einem Hinweis ab, damit kein leerer Prompt unbemerkt in den Betrieb geht.

### 4. Fachmodule schreiben

Markdown-Dateien in `knowledge/`. Bewaehrter Aufbau:

* `# Titel` als erste Zeile - er wird zum Dokumenttitel und ist durchsuchbar
* `Massgeblich: § ... , § ...` als zweite Zeile - diese Normen werden
  automatisch **jedem** Abschnitt des Moduls als Fundstelle mitgegeben, damit
  eine Suche nach der Norm das Modul findet
* `##`-Abschnitte fuer Tatbestandsmerkmale, Pruefschemata, Buchungstabellen
* Jede Zahl, die sich aendern kann, mit Stand versehen und mit dem Hinweis,
  sie vor der Anwendung gegen die Primaerquelle zu pruefen

Eine `00_hinweis.md` sollte klarstellen, dass die Module Sekundaerquellen
sind und amtliche Quellen Vorrang haben.

### 5. Testfaelle hinterlegen

`testcases.json` nach dem Muster des Buchhalters: je Fall Frage, erwartete
Stichworte und erwartete Normen. Der vorhandene Test
`tests/test_fachliche_faelle.py` prueft damit automatisch, ob die Recherche
zu jedem Fall das richtige Material findet.

### 6. Aktivieren

In `config/settings.json`:

```json
{ "app": { "profile": "controller", "name": "Portabler Controller" } }
```

Oder zum Ausprobieren:

```
KIM_APP_PROFILE=controller python portable_buchhalter.py check
```

### 7. Pruefen

```
python portable_buchhalter.py check
python -m pytest tests -q
```

Die Systempruefung muss die Fachmodule des neuen Profils aufnehmen und
indexieren.

## Gemeinsame Nutzung mehrerer Mitarbeiter

Mehrere Profile koennen **dasselbe** Unternehmensgedaechtnis nutzen - genau
das ist der Sinn der Trennung von Fach- und Unternehmenswissen. Der
Controller weiss dann ohne erneutes Onboarding, dass das Unternehmen SKR03
verwendet.

Zwei Betriebsarten sind moeglich:

**Getrennte Datentraeger** je Mitarbeiter - einfach, aber das
Unternehmenswissen muss gepflegt oder exportiert und importiert werden
(`wissen export` und die Importfunktion des Gedaechtnisses).

**Ein Datentraeger, mehrere Profile** - ein gemeinsames `company.db`, je
Profil ein eigener Fachwissensindex. Dafuer ist eine Auswahl beim Start
vorzusehen (`PORTABLE_UNTERNEHMENS_KI.exe` nach Masterprompt 54). Die
Architektur steht dem nicht im Weg; umgesetzt ist die Auswahl noch nicht -
das ist die naechste sinnvolle Ausbaustufe.

## Was am Core zu aendern waere

Fuer einen weiteren Fachmitarbeiter: **nichts**. Aendert die neue Rolle
grundlegend die Arbeitsweise (etwa Bildauswertung oder Tabellenkalkulation
als Kernfunktion), kommt ein neues Modul unter `src/pkc/` hinzu - das Profil
schaltet es ueber `capabilities` frei.
