"""
build_summary.py — Tournament Summary builder.

Fetches data, formats it into a summary embed, and posts it.
"""

import os
from dotenv import load_dotenv
import json
import sys

from sumo_hooks import SumoAPIClient, post_webhook
from sumo_data import (
    get_previous_basho,
    get_current_basho_id,
    get_next_basho,
    BashoData,
    SummaryData,
    ansi,
    ansi_block,
    RANK_ANSI,
    SPECIAL_PRIZES,
)


# ── Summary-specific formatting ──────────────────────────────────

WIDTH = 40
RULE = "═" * WIDTH
THIN_RULE = "─" * WIDTH


DIVISION_COL = 10
PRIZE_COL = 10
NAME_COL = 12


def _center(text: str) -> str:
    """Center plain text within WIDTH columns.

    Always call this BEFORE ansi() — escape codes count toward len() but
    have no visible width, so centering colored text pulls it off-center.
    Lines longer than WIDTH are returned unpadded.
    """
    return text.center(WIDTH).rstrip()


def _shikona(full_name: str) -> str:
    """Surname only, clipped to the name column.

    The yusho/specialPrizes payloads carry the full name ("Kirishima
    Tetsuo"), unlike banzuke which is already surname-only. The given name
    would overflow NAME_COL and break the column alignment.
    """
    return str(full_name).split(" ")[0][:NAME_COL]


def _award_row(label: str, label_width: int, full_name: str) -> str:
    """A label column and a name column, each centered within its own width.

    Every row comes out the same total width, so once _center() places the
    row the columns line up down the block regardless of name length.
    """
    return f"{label.center(label_width)} • {_shikona(full_name).center(NAME_COL)}"


def _division_ansi(division: str) -> tuple:
    """(fg, style) for a division, borrowed from the shared RANK_ANSI map.

    Divisions have no colors of their own, so the six of them are mapped onto
    the six rank colors by seniority: the top division takes the top rank's
    color, and so on down. Matched on the full name, not the initial —
    division initials collide (Makuuchi/Makushita, Juryo/Jonidan/Jonokuchi).
    """
    divisions = ("Makuuchi", "Juryo", "Makushita",
                 "Sandanme", "Jonidan", "Jonokuchi")
    ranks = ("Y", "O", "S", "K", "M", "J")  # RANK_ANSI keys, most senior first
    rank_key = dict(zip(divisions, ranks)).get(division, "")
    return RANK_ANSI.get(rank_key, ("white", None))


def build_summary_text(basho_id, summary_data: SummaryData) -> str:

    target_basho = BashoData(basho_id)
    next_basho = BashoData(get_next_basho(basho_id))
    lines = []

    # Header
    lines.append(RULE)
    lines.append(ansi(
        _center(f"{target_basho.year} {target_basho.month_name_full} {target_basho.name}"),
        fg="yellow", style="bold"))
    lines.append(ansi(_center("SUMMARY"), fg="yellow"))
    lines.append(_center(f"{target_basho.start_date_str} - {target_basho.end_date_str}"))
    lines.append(_center(f"{target_basho.city}, Japan"))
    lines.append(_center(target_basho.venue_name))
    lines.append(RULE)
    lines.append("")

    # Yusho Winners — one line per division, colored by division.
    lines.append(ansi(_center("🏆 YUSHO WINNERS 🏆"), fg="yellow", style="bold"))
    lines.append("")
    if summary_data.yusho:
        for y in summary_data.yusho:
            division = str(y.get("type"))
            fg, style = _division_ansi(division)
            row = _award_row(division, DIVISION_COL, y.get("shikonaEn"))
            lines.append(ansi(_center(row), fg=fg, style=style))
    else:
        lines.append(_center("None"))
    lines.append("")

    # Special Prizes — English name on its own line beneath each winner.
    lines.append(ansi(_center("🎌 SPECIAL PRIZES 🎌"), fg="red", style="bold"))
    lines.append("")
    if summary_data.special_prizes:
        for p in summary_data.special_prizes:
            prize_type = str(p.get("type"))
            english, _reason = SPECIAL_PRIZES.get(prize_type, (prize_type, ""))
            row = _award_row(prize_type, PRIZE_COL, p.get("shikonaEn"))
            lines.append(ansi(_center(row), fg="red"))
            lines.append(ansi(_center(f"({english})"), fg="white"))
    else:
        lines.append(_center("None"))
    lines.append("")

    # Next Tournament
    lines.append(THIN_RULE)
    lines.append(ansi(_center("SEE YOU NEXT TOURNAMENT!"), fg="green", style="bold"))
    lines.append(_center(next_basho.name))
    lines.append(_center(f"{next_basho.start_date_str} — {next_basho.end_date_str}"))
    lines.append(_center(f"{next_basho.city}, Japan"))
    lines.append(_center(next_basho.venue_name))
    lines.append(RULE)

    return "\n".join(lines)


def generate_summary(target_basho_id: str):
    client = SumoAPIClient()

    prior_basho_id = get_previous_basho(target_basho_id)

    # torikumi_data = client.get_torikumi(target_basho_id)
    prior_torikumi = client.get_torikumi(prior_basho_id, day=15)

    basho = BashoData(prior_basho_id)
    summary = SummaryData(prior_torikumi)

    content = build_summary_text(prior_basho_id, summary)

    payload = {
        "username": "Sumo-hooks",
        "avatar_url": "",
        "content": f"The {basho.year} {basho.name} is concluded. Click the spoiler to show results.",
        "embeds": [
            {
                "author": {

                },
                "title": "",
                "description": f"|| {ansi_block(content)} ||",
                "color": basho.color,
                "fields": [],
                "thumbnail": {"url": ""},
                "image": {

                },
                "footer": {

                },
            }
        ],
    }

    print("=" * 40)
    print(json.dumps(payload, indent=4))
    print("=" * 40)
    return payload


if __name__ == "__main__":
    load_dotenv()
    # We will just print to console, unless a specific flag is passed down the line.
    
    b = get_current_basho_id()
    payload = generate_summary(b)
    
    # We leave post_webhook available here, if desired, but we won't call it blindly to avoid testing with proper endpoints.
    if len(sys.argv) > 1 and sys.argv[1] == "--post":
        endpoints = os.getenv("testpoint", "").split(",")
        post_webhook(payload, endpoints)
    else:
        print("Run with '--post' to actually post to webhooks.")
