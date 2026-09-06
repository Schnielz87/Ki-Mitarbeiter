<#
.SYNOPSIS
    Baut PORTABLE_BUCHHALTER.exe und stellt den fertigen portablen Ordner her.

.BESCHREIBUNG
    Dieses Skript laeuft auf einem Windows-Rechner mit Python 3.11 oder neuer.
    Es erzeugt einen Ordner, der eins zu eins auf die externe SSD kopiert
    werden kann. Der spaetere Anwender braucht danach weder Python noch eine
    Entwicklungsumgebung.

.BEISPIEL
    powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
    powershell -ExecutionPolicy Bypass -File build\build_windows.ps1 -Ziel D:\Portable-Buchhalter
#>
param(
    [string]$Ziel = "",
    [switch]$OhneTests
)

$ErrorActionPreference = "Stop"
$Wurzel = Split-Path -Parent $PSScriptRoot
Set-Location $Wurzel

function Schritt($text) { Write-Host "`n=== $text ===" -ForegroundColor Cyan }

Schritt "Python pruefen"
$version = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
Write-Host "  Python $version"
if ([version]$version -lt [version]"3.11") {
    throw "Python 3.11 oder neuer wird benoetigt (gefunden: $version)."
}
& python -c "import tkinter" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Tkinter fehlt in dieser Python-Installation." }

Schritt "Abhaengigkeiten installieren"
& python -m pip install --upgrade pip | Out-Null
& python -m pip install -r requirements.txt
& python -m pip install pyinstaller

if (-not $OhneTests) {
    Schritt "Tests ausfuehren"
    & python -m pytest tests -q
    if ($LASTEXITCODE -ne 0) { throw "Die Tests sind fehlgeschlagen - es wird nicht gebaut." }
}

Schritt "Alten Build entfernen"
Remove-Item -Recurse -Force "build\pyinstaller", "dist" -ErrorAction SilentlyContinue

Schritt "EXE bauen"
& python -m PyInstaller --clean --noconfirm `
    --distpath dist --workpath build\pyinstaller `
    build\portable_buchhalter.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller ist fehlgeschlagen." }

$Ausgabe = "dist\PORTABLE_BUCHHALTER"
foreach ($datei in @("PORTABLE_BUCHHALTER.exe", "PORTABLE_BUCHHALTER_KONSOLE.exe")) {
    if (-not (Test-Path (Join-Path $Ausgabe $datei))) {
        throw "$datei wurde nicht erzeugt - Build gilt als fehlgeschlagen."
    }
}

Schritt "Portablen Ordner zusammenstellen"
if (-not $Ziel) { $Ziel = "dist\Portable-Buchhalter" }
Remove-Item -Recurse -Force $Ziel -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Ziel | Out-Null

# EXE und ihre Bestandteile
Copy-Item "$Ausgabe\*" -Destination $Ziel -Recurse -Force

# Lesbare Bestandteile: Mitarbeiterprofil, Quellenregister, Dokumentation
New-Item -ItemType Directory -Force -Path "$Ziel\src" | Out-Null
Copy-Item "src\profiles" -Destination "$Ziel\src\profiles" -Recurse -Force
New-Item -ItemType Directory -Force -Path "$Ziel\config" | Out-Null
Copy-Item "config\source_registry.json" -Destination "$Ziel\config\" -Force
if (Test-Path "config\model_catalog.json") {
    Copy-Item "config\model_catalog.json" -Destination "$Ziel\config\" -Force
}
if (Test-Path "config\brand.json") {
    Copy-Item "config\brand.json" -Destination "$Ziel\config\" -Force
}

# Branding: Logo und Symbole gehoeren NEBEN die EXE, nicht in deren
# Innenleben. PyInstaller legt Datendateien unter _internal ab - dort sucht
# die Anwendung nicht, denn sie loest ihre Pfade von der portablen Wurzel
# aus auf. Ohne diese Zeilen bliebe das Fenster ohne Logo, obwohl die
# Dateien im Paket steckten. Ausserdem soll der Betreiber das Logo
# austauschen koennen, ohne neu zu bauen.
if (Test-Path "assets") {
    Copy-Item "assets" -Destination "$Ziel\assets" -Recurse -Force
}
# Der Modelldienst (llama.cpp). Ohne ihn kann ein heruntergeladenes Modell
# nicht antworten - fuer llama-cpp-python gibt es keine fertigen Pakete, der
# Kunde muesste sonst einen Compiler einrichten. Liegt der Ordner nicht vor,
# wird trotzdem gebaut: die Anwendung sagt dann ehrlich, dass er fehlt.
if (Test-Path "runtime\llama") {
    New-Item -ItemType Directory -Force -Path "$Ziel\runtime" | Out-Null
    Copy-Item "runtime\llama" -Destination "$Ziel\runtime\llama" -Recurse -Force
    Write-Host "Modelldienst uebernommen: runtime\llama"
} else {
    Write-Host "HINWEIS: runtime\llama fehlt - das Paket enthaelt keinen Modelldienst."
}

New-Item -ItemType Directory -Force -Path "$Ziel\docs" | Out-Null
Copy-Item "docs\*" -Destination "$Ziel\docs\" -Recurse -Force -ErrorAction SilentlyContinue
foreach ($datei in @("START_HIER.md","README.md","ARCHITEKTUR.md","PROJEKTSTATUS.md",
                     "CHANGELOG.md","SICHERHEITSKONZEPT.md","UPDATE_KONZEPT.md",
                     "ERP_CONNECTOR_KONZEPT.md","MEMORY_KONZEPT.md",
                     "DATENSPEICHER_KONZEPT.md","BACKUP_WIEDERHERSTELLUNG.md",
                     "TESTBERICHT.md")) {
    if (Test-Path $datei) { Copy-Item $datei -Destination $Ziel -Force }
}

# Leere Datenverzeichnisse und Markerdatei
foreach ($ordner in @("models","knowledge","resources\raw","resources\normalized",
                      "resources\metadata","resources\index","company","database",
                      "conversations","workspace","connectors","runtime","logs",
                      "updates","backups","data","checkpoints")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Ziel $ordner) | Out-Null
}
"Portable-KI-Mitarbeiter Wurzelverzeichnis.`nDiese Datei nicht loeschen - sie markiert den portablen Datenbestand." |
    Set-Content -Path (Join-Path $Ziel ".portable_root") -Encoding UTF8

Schritt "Rauchtest der gebauten EXE"
# Bewusst die Konsolenfassung: die Fensterfassung hat unter Windows keine
# Standardausgabe, ihr Ergebnis waere hier nicht pruefbar.
$exe = Join-Path $Ziel "PORTABLE_BUCHHALTER_KONSOLE.exe"
& $exe check --quiet | Tee-Object -Variable zeilen
if ($LASTEXITCODE -gt 2) { throw "Die gebaute EXE liess sich nicht ausfuehren." }
if (($zeilen -join "`n") -notmatch "Systempruefung") {
    throw "Die gebaute EXE lieferte eine unerwartete Ausgabe."
}

Schritt "Fertig"
Write-Host "  Portabler Ordner: $Ziel" -ForegroundColor Green
Write-Host "  Diesen Ordner vollstaendig auf die externe SSD kopieren."
Write-Host "  Doppelklick: PORTABLE_BUCHHALTER.exe"
Write-Host "  Kommandozeile: PORTABLE_BUCHHALTER_KONSOLE.exe <befehl>"
Write-Host "  Danach fehlt nur noch das Sprachmodell in .\models (docs\MODELL_EINRICHTEN.md)."
