# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Beschreibung fuer PORTABLE_BUCHHALTER.exe.

Entscheidung: **onedir**, nicht onefile.

Begruendung: Eine onefile-EXE entpackt sich bei jedem Start in das
Windows-Temp-Verzeichnis des jeweiligen Rechners.  Das widerspricht dem
Grundsatz, dass die Anwendung auf dem portablen Datentraeger bleibt
(Masterprompt 20) und macht den Start langsam.  Bei onedir liegt die EXE im
Wurzelverzeichnis, ihre Bestandteile in einem Unterordner daneben - alles auf
der SSD.

Die Mitarbeiterprofile (Masterprompt, Fachmodule) und das Quellenregister
werden bewusst **nicht** in die EXE gepackt, sondern liegen als lesbare
Dateien daneben.  So kann der Betreiber den Fachprompt und die Fachmodule
einsehen und anpassen, ohne neu bauen zu muessen.
"""

import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
ROOT = SPEC_DIR.parent

block_cipher = None

hidden_imports = [
    "app", "app.controller",
    "ui", "ui.cli", "ui.tk_app",
    "pkc", "pkc.paths", "pkc.config", "pkc.logging_setup", "pkc.hardware",
    "pkc.netstate", "pkc.profile", "pkc.checkpoint",
    "pkc.db", "pkc.db.connection", "pkc.db.schema",
    "pkc.memory", "pkc.memory.store", "pkc.memory.capture", "pkc.memory.schema_keys",
    "pkc.knowledge", "pkc.knowledge.extract", "pkc.knowledge.chunker",
    "pkc.knowledge.store", "pkc.knowledge.bundled",
    "pkc.retrieval", "pkc.retrieval.embeddings", "pkc.retrieval.search",
    "pkc.llm", "pkc.llm.base", "pkc.llm.providers", "pkc.llm.manager",
    "pkc.rag", "pkc.rag.context", "pkc.rag.engine",
    "pkc.updater", "pkc.updater.http_client", "pkc.updater.registry",
    "pkc.updater.pipeline",
    "pkc.security", "pkc.security.vault",
    "pkc.audit", "pkc.audit.log", "pkc.audit.approvals",
    "pkc.connectors", "pkc.connectors.base", "pkc.connectors.files",
    "pkc.connectors.rest", "pkc.connectors.erp_stubs", "pkc.connectors.registry",
    # Standardbibliothek, die PyInstaller nicht immer selbst findet
    "sqlite3", "tkinter", "tkinter.ttk", "tkinter.scrolledtext",
    "tkinter.filedialog", "tkinter.messagebox",
]

# Optionale Zusatzpakete nur aufnehmen, wenn sie vorhanden sind.
for optional in ("certifi", "cryptography", "pypdf", "openpyxl", "llama_cpp", "yaml"):
    try:
        __import__(optional)
    except ImportError:
        continue
    hidden_imports.append(optional)

# Der Wurzelspeicher von certifi ist eine Datendatei, kein Modul - PyInstaller
# nimmt sie nur mit, wenn sie ausdruecklich genannt wird. Ohne sie scheitert
# der Abruf von Servern, die ihr Zwischenzertifikat nicht mitliefern.
zertifikate = []
try:
    import certifi

    zertifikate = [(certifi.where(), "certifi")]
except ImportError:
    pass

analysis = Analysis(
    [str(ROOT / "portable_buchhalter.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=zertifikate,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy.distutils", "pytest", "setuptools", "pip"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

def _exe(name: str, console: bool):
    return EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name=name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=console,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )


# Zwei Programme aus demselben Code - wie python.exe und pythonw.exe:
#
#   PORTABLE_BUCHHALTER.exe          fuer den Doppelklick. Ohne Konsole, damit
#                                    kein schwarzes Fenster mit aufgeht.
#   PORTABLE_BUCHHALTER_KONSOLE.exe  fuer die Kommandozeile. MIT Konsole, denn
#                                    ein Programm ohne Konsole hat unter Windows
#                                    keine Ausgabe: "check" oder "wissen get"
#                                    wuerden in der Eingabeaufforderung stumm
#                                    bleiben.
exe_gui = _exe("PORTABLE_BUCHHALTER", console=False)
exe_cli = _exe("PORTABLE_BUCHHALTER_KONSOLE", console=True)

collection = COLLECT(
    exe_gui,
    exe_cli,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PORTABLE_BUCHHALTER",
)
