---
name: Umsatzsteuer-Voranmeldung
kategorie: Steuern
format: docx
beschreibung: Abgabevermerk ueber die vorbereitete Voranmeldung eines Zeitraums.
---
# Umsatzsteuer-Voranmeldung {{zeitraum}}

Unternehmen: {{firma.name}}
Steuernummer: {{firma.steuernummer}}
Bearbeitet von: {{bearbeiter}}, {{datum}}

| Position | Betrag |
| --- | --- |
| Umsaetze zum Regelsteuersatz | {{umsatz.regel}} |
| Umsaetze zum ermaessigten Satz | {{umsatz.ermaessigt}} |
| Steuerfreie Umsaetze | {{umsatz.steuerfrei}} |
| Umsatzsteuer | {{steuer.umsatzsteuer}} |
| Vorsteuer | {{steuer.vorsteuer}} |
| Zahllast bzw. Erstattung | {{steuer.zahllast}} |

## Vermerke

{{vermerke}}

---

Zahlen aus der laufenden Buchhaltung. Vor der Uebermittlung ist die
Voranmeldung durch einen Menschen zu pruefen und freizugeben.
