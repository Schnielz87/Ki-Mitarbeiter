"""Ein PDF ohne Fremdpaket schreiben (Erweiterung E4).

Warum selbst geschrieben: die Anwendung soll Berichte **offline** erzeugen,
ohne installiertes Office und ohne dass ein weiteres Paket auf dem
Datentraeger liegen muss. Ein PDF mit den Standardschriften (Helvetica,
Courier) ist dafuer klein und gut beherrschbar - es braucht keine
Schriftarteneinbettung.

Bewusst nicht enthalten: Bilder, Farben, Umbruchoptimierung, beliebige
Schriften. Was hier entsteht, ist ein sauber lesbarer Fliesstext mit
Ueberschriften, Aufzaehlungen und einfachen Tabellen.
"""

from __future__ import annotations

from .modell import Dokument

#: A4 in Punkten (72 dpi).
BREITE, HOEHE = 595.28, 841.89
RAND_LINKS, RAND_RECHTS = 56.7, 56.7          # 2 cm
RAND_OBEN, RAND_UNTEN = 56.7, 56.7

SCHRIFTEN = {
    "normal": ("F1", "Helvetica", 10.5),
    "fett": ("F2", "Helvetica-Bold", 10.5),
    "h1": ("F2", "Helvetica-Bold", 16.0),
    "h2": ("F2", "Helvetica-Bold", 13.0),
    "h3": ("F2", "Helvetica-Bold", 11.5),
    "fest": ("F3", "Courier", 9.5),
}

#: Mittlere Zeichenbreite je Schrift, als Anteil der Schriftgroesse.
#: Helvetica ist eine Proportionalschrift; fuer den Umbruch genuegt ein
#: vorsichtiger Mittelwert - lieber eine Zeile frueher umbrechen als ueber
#: den Rand hinausschreiben.
_BREITE_ANTEIL = {"F1": 0.52, "F2": 0.55, "F3": 0.60}


def _text_escape(text: str) -> bytes:
    roh = text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    return roh.encode("cp1252", errors="replace")


def _umbrechen(text: str, schrift: str, groesse: float, breite: float) -> list[str]:
    """Bricht einen Absatz auf die verfuegbare Breite um."""
    je_zeichen = _BREITE_ANTEIL[schrift] * groesse
    hoechstens = max(8, int(breite / je_zeichen))
    zeilen: list[str] = []
    for absatz in text.split("\n"):
        worte = absatz.split()
        if not worte:
            zeilen.append("")
            continue
        zeile = worte[0]
        for wort in worte[1:]:
            if len(zeile) + 1 + len(wort) <= hoechstens:
                zeile = f"{zeile} {wort}"
            else:
                zeilen.append(zeile)
                zeile = wort
        zeilen.append(zeile)
    return zeilen


class _Seiten:
    """Sammelt Textzeilen und legt bei Bedarf eine neue Seite an."""

    def __init__(self):
        self.seiten: list[list[bytes]] = [[]]
        self.y = HOEHE - RAND_OBEN

    @property
    def breite(self) -> float:
        return BREITE - RAND_LINKS - RAND_RECHTS

    def _neue_seite(self) -> None:
        self.seiten.append([])
        self.y = HOEHE - RAND_OBEN

    def abstand(self, hoehe: float) -> None:
        if self.y - hoehe < RAND_UNTEN:
            self._neue_seite()
            return
        self.y -= hoehe

    def zeile(self, text: str, stil: str = "normal", einzug: float = 0.0) -> None:
        kennung, _, groesse = SCHRIFTEN[stil]
        zeilenhoehe = groesse * 1.35
        if self.y - zeilenhoehe < RAND_UNTEN:
            self._neue_seite()
        self.y -= zeilenhoehe
        inhalt = (b"BT /" + kennung.encode() + b" " + f"{groesse:.1f}".encode() + b" Tf "
                  + f"{RAND_LINKS + einzug:.2f} {self.y:.2f}".encode() + b" Td ("
                  + _text_escape(text) + b") Tj ET\n")
        self.seiten[-1].append(inhalt)

    def absatz(self, text: str, stil: str = "normal", einzug: float = 0.0) -> None:
        kennung, _, groesse = SCHRIFTEN[stil]
        for zeile in _umbrechen(text, kennung, groesse, self.breite - einzug):
            self.zeile(zeile, stil, einzug)


def _tabellenzeilen(zeilen: list[list[str]]) -> list[str]:
    """Setzt eine Tabelle in fester Schrift - so stehen die Spalten sauber."""
    if not zeilen:
        return []
    spalten = max(len(z) for z in zeilen)
    breiten = [0] * spalten
    for zeile in zeilen:
        for i, wert in enumerate(zeile):
            breiten[i] = max(breiten[i], len(wert))
    raus = []
    for nummer, zeile in enumerate(zeilen):
        gefuellt = list(zeile) + [""] * (spalten - len(zeile))
        raus.append("  ".join(w.ljust(breiten[i]) for i, w in enumerate(gefuellt)).rstrip())
        if nummer == 0:
            raus.append("  ".join("-" * b for b in breiten))
    return raus


def pdf_bytes(dokument: Dokument) -> bytes:
    """Erzeugt ein vollstaendiges PDF."""
    seiten = _Seiten()
    if dokument.titel:
        seiten.absatz(dokument.titel, "h1")
        seiten.abstand(6)

    for block in dokument.bloecke:
        if block.art == "ueberschrift":
            seiten.abstand(8)
            seiten.absatz(block.text, {1: "h1", 2: "h2", 3: "h3"}.get(block.ebene, "h3"))
        elif block.art == "absatz":
            seiten.abstand(4)
            seiten.absatz(block.text, "normal")
        elif block.art == "aufzaehlung":
            seiten.abstand(4)
            for punkt in block.punkte:
                zeilen = _umbrechen(punkt, "F1", SCHRIFTEN["normal"][2], seiten.breite - 18)
                for nummer, zeile in enumerate(zeilen):
                    seiten.zeile(("- " if nummer == 0 else "  ") + zeile, "normal", 12)
        elif block.art == "code":
            seiten.abstand(4)
            for zeile in block.text.splitlines():
                seiten.zeile(zeile, "fest", 12)
        elif block.art == "tabelle":
            seiten.abstand(6)
            for zeile in _tabellenzeilen(block.zeilen):
                seiten.zeile(zeile, "fest", 0)

    return _zusammensetzen(seiten.seiten, dokument.titel)


def _zusammensetzen(seiteninhalte: list[list[bytes]], titel: str) -> bytes:
    objekte: list[bytes] = []

    def hinzu(inhalt: bytes) -> int:
        objekte.append(inhalt)
        return len(objekte)          # 1-basierte Objektnummer

    schriftnummern = {}
    for kennung, name, _ in SCHRIFTEN.values():
        if kennung in schriftnummern:
            continue
        schriftnummern[kennung] = hinzu(
            f"<< /Type /Font /Subtype /Type1 /BaseFont /{name} "
            f"/Encoding /WinAnsiEncoding >>".encode()
        )

    ressourcen = "/Font << " + " ".join(
        f"/{kennung} {nummer} 0 R" for kennung, nummer in schriftnummern.items()
    ) + " >>"

    inhaltsnummern = []
    for inhalt in seiteninhalte:
        strom = b"".join(inhalt)
        inhaltsnummern.append(hinzu(
            b"<< /Length " + str(len(strom)).encode() + b" >>\nstream\n" + strom + b"endstream"
        ))

    seitenbaum = len(objekte) + len(inhaltsnummern) + 1
    seitennummern = []
    for inhaltsnummer in inhaltsnummern:
        seitennummern.append(hinzu(
            f"<< /Type /Page /Parent {seitenbaum} 0 R "
            f"/MediaBox [0 0 {BREITE:.2f} {HOEHE:.2f}] "
            f"/Resources << {ressourcen} >> /Contents {inhaltsnummer} 0 R >>".encode()
        ))
    baumnummer = hinzu(
        ("<< /Type /Pages /Kids [" + " ".join(f"{n} 0 R" for n in seitennummern)
         + f"] /Count {len(seitennummern)} >>").encode()
    )
    assert baumnummer == seitenbaum, "Seitenbaumnummer muss vorab stimmen"
    katalog = hinzu(f"<< /Type /Catalog /Pages {baumnummer} 0 R >>".encode())
    info = hinzu(b"<< /Title (" + _text_escape(titel or "Bericht")
                 + b") /Producer (PORTIVA) >>")

    raus = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    stellen = []
    for nummer, inhalt in enumerate(objekte, start=1):
        stellen.append(len(raus))
        raus += f"{nummer} 0 obj\n".encode() + inhalt + b"\nendobj\n"

    xref = len(raus)
    raus += f"xref\n0 {len(objekte) + 1}\n".encode()
    raus += b"0000000000 65535 f \n"
    for stelle in stellen:
        raus += f"{stelle:010d} 00000 n \n".encode()
    raus += (f"trailer\n<< /Size {len(objekte) + 1} /Root {katalog} 0 R "
             f"/Info {info} 0 R >>\nstartxref\n{xref}\n%%EOF\n").encode()
    return bytes(raus)
