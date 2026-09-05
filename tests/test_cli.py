"""Kommandozeile: die Schalter muessen dort funktionieren, wo man sie erwartet."""

from __future__ import annotations

import pytest

from ui.cli import build_parser


@pytest.mark.parametrize("argumente", [
    ["--quiet", "check"],
    ["check", "--quiet"],
    ["--offline", "--quiet", "check"],
    ["check", "--offline", "--quiet"],
])
def test_global_options_work_in_both_positions(argumente):
    """``check --quiet`` und ``--quiet check`` muessen beide gehen.

    Diese Luecke fiel im Windows-Ablauf auf: der Rauchtest der gebauten EXE
    schlug mit "unrecognized arguments: --quiet" fehl, weil der Schalter nur
    vor dem Unterbefehl erlaubt war.
    """
    args = build_parser().parse_args(argumente)
    assert args.command == "check"
    assert args.quiet is True


def test_option_before_subcommand_is_not_overwritten():
    """Ein vorne gesetzter Schalter darf hinten nicht auf den Standard zurueckfallen."""
    args = build_parser().parse_args(["--quiet", "--offline", "frage", "Testfrage"])
    assert args.quiet is True and args.offline is True
    assert args.frage == "Testfrage"


def test_root_option_in_both_positions(tmp_path):
    vorne = build_parser().parse_args(["--root", str(tmp_path), "status"])
    hinten = build_parser().parse_args(["status", "--root", str(tmp_path)])
    assert vorne.root == hinten.root == str(tmp_path)


def test_all_subcommands_accept_the_global_options():
    parser = build_parser()
    befehle = {
        "check": [], "frage": ["x"], "chat": [], "wissen": ["list"], "update": [],
        "status": [], "onboarding": [], "sicherung": [], "beleg": [], "freigaben": [],
    }
    for befehl, zusatz in befehle.items():
        args = parser.parse_args([befehl, *zusatz, "--quiet"])
        assert args.quiet is True, f"{befehl} nimmt --quiet nicht an"
