"""
build_new_matches.py — Daily Match Card builder.

Fetches data, formats it into the match card embed, and posts it.
All reusable data logic lives in sumo_data.py.
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from sumo_hooks import SumoAPIClient, post_webhook
from sumo_data import (
    parse_short_rank, get_h2h_wins, build_rikishi_stats, BashoData,
    get_current_basho_id, get_current_day
)


# ── Match-card-specific formatting ───────────────────────────────

def format_match_line(rank: str, shikona: str, wins: int, losses: int, h2h_wins: int, form: str) -> tuple[str, str]:
    """Returns a padded string line for the rikishi and their rank initial for coloring."""
    parsed = parse_short_rank(rank)
    short_rank = parsed["short"]
    rank_initial = parsed["initial"]

    record_str = f"{wins}-{losses}"
    record_padded = f"{record_str:>4}"
    h2h_str = f"{h2h_wins:<2}"

    line = f"{short_rank} {shikona:<13} {record_padded:>4} {h2h_str:>3} {form:>5}"
    return line, rank_initial


# ── Build the payload ────────────────────────────────────────────

def build_new_matches_payload(basho_id: str, day: int) -> dict:
    client = SumoAPIClient()

    # Fetch Data
    torikumi_data = client.get_torikumi(basho_id, day=day)
    banzuke_makuuchi = client.get_banzuke(basho_id)
    banzuke_juryo = client.get_banzuke(basho_id, division="Juryo")
    banzuke_data = {
        "east": banzuke_makuuchi.get("east", []) + banzuke_juryo.get("east", []),
        "west": banzuke_makuuchi.get("west", []) + banzuke_juryo.get("west", []),
    }

    # Tournament info for title
    basho = BashoData(torikumi_data)
    
    # Calculate match dates based on tournament start date and day
    raw_start = torikumi_data.get("startDate", "2026-03-08T00:00:00Z")
    start_dt = datetime.fromisoformat(raw_start.replace('Z', '+00:00'))
    
    # Day 1 JST = start_dt. Day n JST = start_dt + (day-1)
    match_dt_jst = start_dt + timedelta(days=day - 1)
    # Japan is 1 day ahead of EST
    match_dt_est = match_dt_jst - timedelta(days=1)
    
    time_str = f"{match_dt_est.strftime('%b %e')} 8PM EST • {match_dt_jst.strftime('%b %e')} 12AM UTC / 9AM JST"
    title = f"{basho.name} — {basho.city}, {basho.month_name_full} {basho.year}"

    # Build stats from common logic
    rikishi_stats = build_rikishi_stats(banzuke_data, day)

    # Iterate torikumi matches
    named_matches = []
    m_matches = []
    matches = torikumi_data.get("torikumi", [])
    for match in matches:
        east_id = match.get("eastId")
        west_id = match.get("westId")

        # Get H2H
        try:
            h2h_data = client.get_h2h(east_id, west_id)
            h2h_matches = h2h_data.get("matches") or []
        except Exception:
            h2h_matches = []

        east_h2h = get_h2h_wins(h2h_matches, east_id)
        west_h2h = get_h2h_wins(h2h_matches, west_id)

        east_stat = rikishi_stats.get(east_id, {})
        west_stat = rikishi_stats.get(west_id, {})

        if not east_stat or not west_stat:
            continue

        east_line, east_rank = format_match_line(
            east_stat["rank"], east_stat["shikona"],
            east_stat["wins"], east_stat["losses"],
            east_h2h, east_stat["form"],
        )
        west_line, west_rank = format_match_line(
            west_stat["rank"], west_stat["shikona"],
            west_stat["wins"], west_stat["losses"],
            west_h2h, west_stat["form"],
        )

        match_str = f"{east_line}\n{west_line}\n" + "-" * 38

        if east_rank in ["Y", "O", "S", "K"] or west_rank in ["Y", "O", "S", "K"]:
            named_matches.append(match_str)
        else:
            m_matches.append(match_str)

    # Construct the output
    header = (
        f"```ml\n🔴 DAY {day} CARD • UPCOMING MATCHES 🔴 \n"
        f"\nRANK     NAME       W-L  VS  FORM\n```"
    )

    matches_text = ""
    if m_matches:
        matches_text += "```\n" + "\n".join(m_matches) + "\n```\n"
    if named_matches:
        matches_text += "```prolog\n" + "\n".join(named_matches) + "\n```\n"

    full_description = f"{header}{matches_text.strip()}"
    footer = (
            f"The fusen wins weren't reflecting in scores properly.\n"
            f"This should now be fixed."
    )

    payload = {
        "username": "Sumo-hooks",
        "content": title,
        "embeds": [
            {
                "title": time_str,
                "description": full_description,
                "color": 2303786,

                "footer": 
                {
                "text": footer,
                "icon_url":""
            }
            
        }
        ],

    }
    return payload


if __name__ == "__main__":
    load_dotenv()
    endpoints = os.getenv("testpoint", "").split(",")
    # Programmatic Discovery
    client = SumoAPIClient()
    basho_id = get_current_basho_id()
    start_date = client.get_basho_start_date(basho_id)
    day = get_current_day(start_date)

    print(f"Targeting Basho: {basho_id}, Day: {day}")
    payload = build_new_matches_payload(basho_id, day)

    print("Sending payload:")
    print(json.dumps(payload, indent=2))
    post_webhook(payload, endpoints)
