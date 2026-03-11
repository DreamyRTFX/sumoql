"""
build_briefing.py — Tournament Briefing builder.

Fetches data, formats it into the briefing embed, and posts it.
All reusable data logic lives in sumo_data.py.
"""

import os
from dotenv import load_dotenv
import json

from sumo_hooks import SumoAPIClient, post_webhook
from sumo_data import (
    parse_short_rank,
    get_previous_basho,
    BashoData,
    SanyakuData,
    StakesData,
)


# ── Briefing-specific formatting helpers ──────────────────────────

def _pair_up(rikishi_list):
    """Yield (east, west) pairs for the sanyaku table display."""
    for i in range(0, len(rikishi_list), 2):
        east = rikishi_list[i]
        west = rikishi_list[i + 1] if i + 1 < len(rikishi_list) else None
        yield east, west


def _format_row(east, west) -> str:
    """Format a single row of the sanyaku table."""
    east_str = ""
    if east:
        parsed = parse_short_rank(f"{east['rank']} {east['number']} {east['side']}")
        east_str = f"{parsed['short']} {east['name']:<12}"

    west_str = ""
    if west:
        parsed = parse_short_rank(f"{west['rank']} {west['number']} {west['side']}")
        west_str = f" | {parsed['short']} {west['name']}"

    return f"{east_str}{west_str}\n"


# ── Build the briefing text ──────────────────────────────────────

def build_briefing_text(basho_data: BashoData, san_yaku_data: SanyakuData, stakes_data: StakesData) -> str:

    out = ""
    out += f"🌸 {basho_data.name.upper()} {basho_data.year} // {basho_data.city.upper()}\n\n"
    out += f"The {basho_data.name} begins in 24 hours.\n\n"

    # Logistics
    out += "**LOGISTICS**\n"
    out += f"Dates: {basho_data.start_date_str} — {basho_data.end_date_str} (JST) \n"
    out += f"Venue: {basho_data.venue_name}\n"
    out += f"Start: {basho_data.daily_start_time} (Daily)\n\n"

    # San'yaku
    out += "**THE SANYAKU**\n"

    if san_yaku_data.yokozuna:
        for east, west in _pair_up(san_yaku_data.yokozuna):
            out += _format_row(east, west)

    for east, west in _pair_up(san_yaku_data.ozeki):
        out += _format_row(east, west)

    for east, west in _pair_up(san_yaku_data.sekiwake):
        out += _format_row(east, west)

    for east, west in _pair_up(san_yaku_data.komusubi):
        out += _format_row(east, west)

    out += "\n"

    # Stakes
    out += "**STATUS**\n"
    out += f"Last Yusho: {stakes_data.defending_champ} {basho_data.prior_basho_label}\n"

    kadoban_str = ", ".join(stakes_data.kadoban) if stakes_data.kadoban else "None"
    out += f"Kadoban: {kadoban_str}\n"
    kyujo_str = ", ".join(stakes_data.kyujo) if stakes_data.kyujo else "None"
    out += f"Kyujo: {kyujo_str}\n"

    return out


# ── Orchestration ─────────────────────────────────────────────────

def generate_announcement(target_basho_id: str):
    client = SumoAPIClient()

    prior_basho_id = get_previous_basho(target_basho_id)

    torikumi_data = client.get_torikumi(target_basho_id)
    banzuke_data = client.get_banzuke(target_basho_id)

    prior_torikumi = client.get_torikumi(prior_basho_id, day=15)
    prior_banzuke = client.get_banzuke(prior_basho_id)

    basho = BashoData(torikumi_data)
    sanyaku = SanyakuData(banzuke_data)
    stakes = StakesData(banzuke_data, torikumi_data, prior_torikumi, prior_banzuke)
    content = build_briefing_text(basho, sanyaku, stakes)
    title = "TOURNAMENT BRIEFING"

    payload = {
        "username": "Sumo-hooks",
        "avatar_url": "",
        "content": "Sumo update",
        "embeds": [
            {
                "author": {
                    "name": f"{basho.year} {basho.name.upper()} // {basho.city}",
                    "url": "https://www3.nhk.or.jp/nhkworld/en/tv/sumo/",
                    "icon_url": "",
                },
                "title": title,
                "url": "https://www3.nhk.or.jp/nhkworld/en/tv/sumo/",
                "description": f"```\n{content}```",
                "color": 13845190,
                "fields": [],
                "thumbnail": {"url": ""},
                "image": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/EDION_Arena_Osaka.JPG/960px-EDION_Arena_Osaka.JPG"
                },
                "footer": {
                    "text": "Osaka Prefectural Gymnasium",
                    "icon_url": "",
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
    endpoints = os.getenv("endpoints", "").split(",")
    testpoint = os.getenv("testpoint", "").split(",")

    payload = generate_announcement("202603")
    post_webhook(payload, testpoint)
