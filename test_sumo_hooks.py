"""
test_sumo_hooks.py — Tests for builder-specific formatting functions.

Common data logic tests are in test_sumo_data.py.
"""

import pytest
from build_new_matches import format_match_line


def test_format_match_line_structure():
    """Verify the formatted line has the correct structure and content."""
    line, rank_initial = format_match_line(
        rank="Yokozuna 1 East",
        shikona="Terunofuji",
        wins=10,
        losses=2,
        h2h_wins=14,
        form="○○●○○",
    )
    assert rank_initial == "Y"
    assert line.strip().startswith("Y1e")
    assert "Terunofuji" in line
    assert "10-2" in line
    assert "14" in line
    assert "○○●○○" in line


def test_format_match_line_maegashira():
    """Verify Maegashira rank formatting."""
    line, rank_initial = format_match_line(
        rank="Maegashira 14 East",
        shikona="Ryuden",
        wins=3,
        losses=5,
        h2h_wins=0,
        form="●○○●○",
    )
    assert rank_initial == "M"
    assert "M14e" in line
    assert "Ryuden" in line
    assert "3-5" in line


def test_format_match_line_zero_h2h():
    """Verify H2H displays correctly when there are no prior meetings."""
    line, _ = format_match_line(
        rank="Sekiwake 1 West",
        shikona="Hoshoryu",
        wins=0,
        losses=0,
        h2h_wins=0,
        form="",
    )
    assert "S1w" in line
    assert "0-0" in line
