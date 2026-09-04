# ERP- und Connector-Konzept

Masterprompt Abschnitt 40.

## Ehrlicher Stand

| Connector | Stand | Sofort nutzbar |
|---|---|---|
| CSV | vollstaendig umgesetzt | **ja** |
| Excel | umgesetzt, benoetigt `openpyxl` | ja, sofern das Paket vorhanden ist |
| Generisches REST | vollstaendig umgesetzt | ja, nach Konfiguration |
| SAP | **nicht angebunden** | nein |
| Wilken | **nicht angebunden** | nein |
| DATEV | **nicht angebunden** | nein |

Die drei ERP-Systeme sind bewusst **keine** Attrappen, die Daten
vortaeuschen. Sie melden klar, dass sie nicht angebunden sind, und nennen die
Fragen, die vor einer Integration zu klaeren sind. Ein Aufruf liefert eine
Fehlermeldung, niemals erfundene Datensaetze.

Der Grund ist sachlich: Eine echte ERP-Anbindung braucht Angaben, die nur der
Betreiber liefern kann - Produktversion, Schnittstellenart, Zugaenge,
Netzwerkfreigaben, Berechtigungen und eine Testumgebung.

## Feste Regeln

### 1. Standard ist READ ONLY

Jeder Connector startet im Modus `read_only`. Ein Schreibversuch schlaegt
fehl - technisch, nicht nur dokumentarisch. Schreiben verlangt eine
ausdrueckliche Umstellung auf `read_write` in der Konfiguration.

### 2. Schreiben nur mit Freigabe

```
VORSCHLAG  ->  VORSCHAU  ->  MENSCHLICHE FREIGABE  ->  AUSFUEHRUNG  ->  PROTOKOLL
```

* **Vorschlag**: `propose_write()` legt einen Freigabevorgang an
* **Vorschau**: `preview_write()` zeigt, was geschrieben wuerde - und
  schreibt nachweislich nichts
* **Freigabe**: ein Mensch setzt den Vorgang auf `FREIGEGEBEN`
* **Ausfuehrung**: `write()` prueft die Freigabe und bricht sonst ab
* **Protokoll**: Zeitpunkt, Freigabe, Connector und Ergebnis werden
  festgehalten

### 3. Zugangsdaten nur aus dem Tresor

Kein Passwort und kein Token steht in einer Konfigurationsdatei. Ein
Connector erhaelt nur einen Schluesselnamen und holt den Wert aus dem
verschluesselten Tresor.

## Konfiguration

In `config/settings.json`:

```json
{
  "connectors": {
    "default_mode": "read_only",
    "settings": {
      "csv":   { "directory": "workspace/import" },
      "excel": { "directory": "workspace/import" },
      "generic_rest": {
        "base_url": "https://erp.example.local/api",
        "secret_key": "erp_token",
        "auth_scheme": "Bearer",
        "health_path": "health",
        "rows_key": "items",
        "timeout": 30
      }
    }
  }
}
```

## Vor einer echten Anbindung zu klaeren

### SAP

1. Version und Release (ECC 6.0, S/4HANA on premise, S/4HANA Cloud)?
2. Steht ein SAP Gateway mit OData-Services zur Verfuegung?
3. Ist RFC/BAPI-Zugriff erlaubt, gibt es einen technischen Benutzer?
4. Welche Berechtigungsobjekte hat dieser Benutzer - nur lesend?
5. VPN oder Netzwerkfreigabe erforderlich?
6. Gibt es ein Qualitaetssystem fuer Tests?
7. Welche Belegarten und Buchungskreise sind relevant?

Moegliche Wege: OData ueber SAP Gateway (bevorzugt), RFC/BAPI, CDS-Views,
Dateiexport.

### Wilken

1. Welches Produkt und welche Version (Wilken P/5, Wilken ERP)?
2. Welche Schnittstellen sind lizenziert und freigeschaltet?
3. Lesender Datenbankzugriff erlaubt oder ausschliesslich API?
4. Welche Mandanten und Buchungskreise?
5. Wie erfolgt die Authentifizierung?

Moegliche Wege: REST, SOAP, lesende Datenbanksicht, Dateiimport.

### DATEV

1. Austausch ueber DATEV-Format-Dateien (EXTF) oder ueber DATEVconnect?
2. Beraternummer und Mandantennummer?
3. Kontenrahmen (SKR03/SKR04) und Sachkontenlaenge?
4. Wer besitzt die Zugaenge und Zertifikate?
5. Sollen Buchungsstapel nur erzeugt oder auch uebertragen werden?

Moegliche Wege: DATEV-Format (EXTF) als Dateiimport und -export - der
praktikabelste erste Schritt -, DATEVconnect, DATEV Unternehmen online.

**Empfehlung:** Mit dem DATEV-Format beginnen. Es braucht keine Zugaenge,
keine Freischaltung und kein VPN; der erzeugte Stapel wird vom Menschen
geprueft und importiert. Das erfuellt die Freigabepflicht auf natuerliche
Weise.

## Neuen Connector ergaenzen

1. Klasse von `Connector` ableiten (`src/pkc/connectors/`)
2. `connector_id`, `name`, `system`, `capabilities`, `open_questions` setzen
3. `configured()` ehrlich beantworten - kein „ja" ohne echte Pruefung
4. `read()` umsetzen; fuer Schreibvorgaenge `_perform_write()`
5. In `CONNECTOR_CLASSES` in `registry.py` eintragen

Die Freigabepflicht und die Modusregel gelten dann automatisch; sie liegen in
der Basisklasse und muessen nicht wiederholt werden.

## Geprueft durch

Standardmodus aller Connectoren ist `read_only`; Schreiben ohne Modus und
ohne Freigabe scheitert; nicht angebundene ERP-Systeme melden das ehrlich und
liefern keine Daten; die Vorschau schreibt nichts; der CSV-Connector liest
eine echte Datei mit deutschem Trennzeichen und deutscher Zahlenschreibweise.
