# Sicherheitskonzept

Masterprompt Abschnitte 21, 41, 42.

## Bedrohungslage

Der Datentraeger enthaelt Unternehmensdaten und wird bewusst zwischen
Rechnern bewegt. Die wichtigsten Risiken:

| Risiko | Antwort |
|---|---|
| Datentraeger geht verloren oder wird gestohlen | Vollverschluesselung des Datentraegers (BitLocker/VeraCrypt) **plus** verschluesselter Tresor fuer Zugangsdaten |
| Fremder PC liest mit | Es bleiben keine Daten auf dem Gastrechner zurueck |
| Zugangsdaten im Klartext | Passwoerter und Tokens ausschliesslich im verschluesselten Tresor |
| Unbemerkte Datenveraenderung | Pruefsummen, Integritaetspruefung, Versionierung, Protokoll |
| Ungewollte Ausfuehrung im ERP | Freigabepflicht, technisch erzwungen |
| Erfundene Rechtsaussagen | Fundstellenzwang und Halluzinationsschutz |

## 1. Verschluesselung des Datentraegers (dringend empfohlen)

Die Anwendung verschluesselt **nicht** den ganzen Datentraeger - das ist
Aufgabe des Betriebssystems und dort besser aufgehoben.

**Windows Pro/Enterprise:** BitLocker To Go. Rechtsklick auf das Laufwerk →
„BitLocker aktivieren", Wiederherstellungsschluessel getrennt vom
Datentraeger aufbewahren.

**Ohne BitLocker:** VeraCrypt-Container.

Ohne diese Massnahme ist bei Verlust des Datentraegers alles lesbar - mit
Ausnahme des Tresors.

## 2. Geheimnistresor

Zugangsdaten gehoeren **nicht** ins Unternehmensgedaechtnis, sondern in
`config/secrets.enc`.

| Eigenschaft | Umsetzung |
|---|---|
| Schluesselableitung | scrypt (N = 32768, r = 8, p = 1) - bewusst rechenintensiv gegen Ausprobieren |
| Verschluesselung | AES-256-GCM, authentifiziert (Manipulation wird erkannt) |
| Zufallswerte | Salt 16 Byte, Nonce 12 Byte, je Schreibvorgang neu |
| Speicherung | atomar ueber eine Nebendatei |

Ohne das Paket `cryptography` wird der Tresor **nicht** benutzt und es
erscheint eine klare Meldung. Es wird nichts unverschluesselt abgelegt und
keine Scheinverschluesselung vorgetaeuscht.

Geprueft: der Klartext eines Geheimnisses ist in der Datei nachweislich nicht
enthalten; ein falsches Passwort fuehrt zu einer verstaendlichen Fehlermeldung;
ein verschlossener Tresor gibt nichts heraus.

**Das Tresorpasswort ist nicht wiederherstellbar.** Geht es verloren, sind
die Geheimnisse verloren - die uebrigen Daten bleiben unberuehrt.

## 3. Freigaben (Human-in-the-Loop)

```
ENTWURF -> GEPRUEFT -> FREIGEGEBEN -> AUSGEFUEHRT
   |          |             |
   +----------+-------------+--> ABGELEHNT
```

Ohne den Zustand `FREIGEGEBEN` ist eine Ausfuehrung **technisch gesperrt** -
nicht nur dokumentarisch. Der Aufruf schlaegt mit einer Fehlermeldung fehl.

Freigabepflichtig: Buchungen, Exporte, ERP-Schreibvorgaenge, Zahlungen,
Behoerdenmeldungen, Stammdatenaenderungen.

Zusaetzlich stehen Connectoren standardmaessig auf **READ ONLY**. Schreiben
verlangt zweierlei: eine ausdrueckliche Umstellung des Modus **und** eine
gueltige Freigabe.

Jede Entscheidung wird mit Zeitpunkt, Person, Zustandswechsel und Begruendung
protokolliert.

## 4. Protokoll

`audit_log` in der Unternehmensdatenbank haelt fest: Start und Ende, Fragen
(ohne den Fragetext), gespeichertes und geloeschtes Unternehmenswissen,
Onboarding, Belegaufnahme, Wissensupdates und deren Ruecknahme,
Einstellungsaenderungen, Sicherungen, Freigabeentscheidungen und
Connector-Zugriffe.

Abschaltbar ueber `security.audit_enabled` - dann fehlt allerdings der
Nachweis.

## 5. Halluzinationsschutz

Technisch durchgesetzt, nicht nur im Prompt gefordert:

| Massnahme | Wirkung |
|---|---|
| Fundstellenzwang | Nur die tatsaechlich gefundenen Fundstellen stehen im Kontext, nummeriert |
| Nummernpruefung | Zitiert das Modell eine Nummer, die es nicht gab, wird sie entfernt und der Nutzer informiert |
| Quellenteil erzwungen | Fehlt er in der Antwort, wird er aus den tatsaechlich verwendeten Fundstellen ergaenzt |
| Wissensstand erzwungen | Jede Antwort nennt Stand und Betriebsart |
| Kein Modell, keine Fachantwort | Ohne Sprachmodell wird **nicht** formuliert, sondern die Lage genannt und die Fundstellen ausgegeben |
| Keine Erfolgsbehauptung | „gespeichert", „getestet", „abgerufen" nur, wenn es tatsaechlich geschah |
| Quellenhierarchie | Sekundaerquellen koennen Primaerrecht nicht ueberstimmen |
| Zeitbezug | Fundstellen tragen Gueltigkeitszeitraeume; historische Sachverhalte werden nicht automatisch nach heutigem Recht beurteilt |

## 6. Netzverhalten

* Es wird nur abgerufen, was im Quellenregister steht.
* `robots.txt` wird beachtet, Wartezeit je Host eingehalten, ein eindeutiger
  User-Agent gesendet.
* Antwortgroesse begrenzt (60 MB), Zeitueberschreitungen abgefangen.
* Ein Online-Sprachmodell wird **nur** nach ausdruecklicher Freigabe benutzt
  (`network.allow_online_llm`, Standard aus).
* Ohne Freigabe verlaesst kein Unternehmensinhalt den Datentraeger.

## 7. Was dieses Konzept **nicht** leistet

Ehrlich benannte Grenzen:

* Keine Benutzerverwaltung und keine Rollentrennung innerhalb der Anwendung -
  wer den Datentraeger und das Passwort hat, hat Zugriff.
* Keine Absicherung gegen einen kompromittierten Gastrechner (Tastatur-
  mitschnitt, Schadsoftware). Der Datentraeger darf nur an vertrauenswuerdigen
  Rechnern verwendet werden.
* Keine Signatur der Programmdateien - die EXE ist nicht codesigniert.
  Windows SmartScreen wird beim ersten Start warnen.
* Keine revisionssichere Archivierung im Sinne der GoBD. Diese Anwendung ist
  Arbeitsmittel, nicht das fuehrende Buchhaltungssystem.
* Das Protokoll ist nicht faelschungssicher - wer die Datenbankdatei
  verandern kann, kann es aendern.

## 8. Empfohlene Betriebsregeln

1. Datentraeger verschluesseln.
2. Tresorpasswort getrennt vom Datentraeger aufbewahren.
3. Regelmaessig sichern (`sicherung`), Sicherung an einem anderen Ort ablegen.
4. Den Datentraeger nur an vertrauenswuerdigen Rechnern verwenden.
5. Keine personenbezogenen Daten aufnehmen, die dort nicht hingehoeren.
6. Vor der Weitergabe des Datentraegers: `company/`, `database/`,
   `conversations/` und `workspace/` pruefen.
