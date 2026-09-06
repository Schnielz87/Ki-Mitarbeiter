"""Plugin- und Erweiterungssystem (Erweiterung E5, Abschnitte 98 bis 123)."""

from .kontext import Pluginkontext, Werkzeug
from .modell import (
    API_VERSION, BERECHTIGUNGEN, KATEGORIEN, SCHWERWIEGEND,
    BerechtigungFehlt, Manifest, PluginFehler,
)
from .paket import ENDUNG, Paketpruefung, packen, pruefen, signaturdaten
from .verwaltung import Pluginstand, Pluginverwaltung

__all__ = [
    "API_VERSION", "BERECHTIGUNGEN", "KATEGORIEN", "SCHWERWIEGEND",
    "BerechtigungFehlt", "Manifest", "PluginFehler",
    "Pluginkontext", "Werkzeug",
    "ENDUNG", "Paketpruefung", "packen", "pruefen", "signaturdaten",
    "Pluginstand", "Pluginverwaltung",
]
