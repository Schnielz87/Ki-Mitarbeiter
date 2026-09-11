---
name: Anlagenverzeichnis (AfA)
kategorie: Abschluss
format: xlsx
beschreibung: Anlagegueter mit Abschreibung und Buchwert zum Stichtag.
---
# Anlagenverzeichnis {{firma.name}}

Stichtag: {{stichtag}}
Erstellt am: {{datum}} von {{bearbeiter}}

| Anlagegut | Anschaffung | Anschaffungswert netto | Nutzungsdauer | AfA pro Jahr | AfA kumuliert | Buchwert |
| --- | --- | --- | --- | --- | --- | --- |
| {{anlage.1.name}} | {{anlage.1.anschaffung}} | {{anlage.1.wert}} | {{anlage.1.dauer}} | {{anlage.1.afa_jahr}} | {{anlage.1.afa_kumuliert}} | {{anlage.1.buchwert}} |
| {{anlage.2.name}} | {{anlage.2.anschaffung}} | {{anlage.2.wert}} | {{anlage.2.dauer}} | {{anlage.2.afa_jahr}} | {{anlage.2.afa_kumuliert}} | {{anlage.2.buchwert}} |
| {{anlage.3.name}} | {{anlage.3.anschaffung}} | {{anlage.3.wert}} | {{anlage.3.dauer}} | {{anlage.3.afa_jahr}} | {{anlage.3.afa_kumuliert}} | {{anlage.3.buchwert}} |

## Hinweis

Die Abschreibung ist monatsgenau gerechnet; der Anschaffungsmonat zaehlt
voll. Betraege in Euro.
