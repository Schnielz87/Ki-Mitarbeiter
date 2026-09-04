# E-Rechnung

## Begriff

Eine E-Rechnung im Sinne des Umsatzsteuerrechts ist eine Rechnung, die in
einem **strukturierten elektronischen Format** ausgestellt, uebermittelt und
empfangen wird und eine **elektronische Verarbeitung** ermoeglicht. Das
Format muss der europaeischen Norm **EN 16931** entsprechen.

Eine PDF-Datei ohne strukturierte Daten ist **keine** E-Rechnung in diesem
Sinne, sondern eine "sonstige Rechnung".

## Zulaessige Formate in Deutschland

* **XRechnung** - reines XML, Standard der KoSIT, im oeffentlichen Auftrags-
  wesen etabliert
* **ZUGFeRD ab Version 2.x** (Profile ab EN-16931-Konformitaet) - hybrides
  Format: PDF/A-3 mit eingebetteter XML-Datei. Massgeblich ist der
  **XML-Teil**; bei Abweichungen zwischen Bildteil und XML gilt der
  strukturierte Datensatz.
* Andere Formate sind zulaessig, wenn sie EN 16931 entsprechen oder die
  erforderlichen Angaben richtig und vollstaendig extrahiert werden koennen.

## Pflicht im inlaendischen B2B-Bereich

Fuer Umsaetze zwischen inlaendischen Unternehmern gilt eine gesetzliche
E-Rechnungspflicht mit gestaffelten Uebergangsfristen. **Empfangsbereitschaft**
war dabei frueher herzustellen als die Pflicht zur Ausstellung. Die konkreten
Stichtage und Uebergangsregelungen sind vor jeder Aussage gegen die
Primaerquelle (§ 14 UStG in der jeweiligen Fassung und die zugehoerigen
BMF-Schreiben, Quellen Q01 und Q02) zu pruefen - sie wurden mehrfach
angepasst. Diese Anwendung nennt hier bewusst **keine** Stichtage aus dem
Gedaechtnis.

Ausgenommen sind unter anderem Kleinbetragsrechnungen nach § 33 UStDV und
Fahrausweise nach § 34 UStDV.

## Aufbewahrung

Der strukturierte Teil der E-Rechnung ist im **Originalformat** und
unveraenderbar aufzubewahren (GoBD). Ein Ausdruck oder eine reine
PDF-Ablage genuegt nicht.

## Pruefschema fuer eingehende E-Rechnungen

1. Liegt ein strukturiertes Format vor (XML bzw. eingebettetes XML)?
2. Ist das XML technisch valide (Schema- und Schematron-Pruefung)?
3. Sind alle Pflichtangaben nach § 14 Abs. 4 UStG im Datensatz enthalten?
4. Stimmen Bildteil und XML bei hybriden Formaten ueberein? Bei Abweichung
   gilt das XML - die Abweichung ist zu dokumentieren.
5. Wird das Original revisionssicher archiviert?
6. Ist der Vorsteuerabzug damit belegt?
