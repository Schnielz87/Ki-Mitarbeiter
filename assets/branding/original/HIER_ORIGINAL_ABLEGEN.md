# Originallogo hier ablegen

In diesem Ordner gehoert die **unveraenderte** Originaldatei des
PORTIVA-Logos:

    assets/branding/original/portiva_logo_original.png

## Warum sie nicht schon da ist

Die Datei muss vom Auftraggeber stammen. Sie wurde im Gespraech als Bild
uebermittelt, erreichte die Entwicklungsumgebung aber nur zur Ansicht und
nicht als Datei auf der Platte. Ein nachgebautes Logo waere ausdruecklich
untersagt - und waere auch das Falsche: es waere nicht Ihre Marke.

## Was zu tun ist

1. Die Originaldatei als `portiva_logo_original.png` in **diesen** Ordner
   legen. Der Dateiname zaehlt.
2. Einmal ausfuehren:

       python tools/branding_ableiten.py

   Daraus entstehen automatisch:

   - `assets/branding/portiva_logo_primary.png`
   - `assets/branding/portiva_logo_light.png`
   - `assets/branding/portiva_logo_dark.png`
   - `assets/branding/portiva_icon.png`
   - `assets/branding/portiva_icon.ico` (16 bis 256 Pixel)

3. Die Originaldatei bleibt unangetastet. Alle Varianten werden aus ihr
   erzeugt und sind damit nachvollziehbar.

## Bis dahin

Die Anwendung laeuft vollstaendig. Sie zeigt an den Stellen, an denen das
Logo stuende, den Schriftzug PORTIVA - und meldet in der Systempruefung,
welche Brandingdateien fehlen. Es wird kein Ersatzlogo erfunden.
