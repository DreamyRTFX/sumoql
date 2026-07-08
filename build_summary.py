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
    SummaryData
)


def build_summary_text(basho_id, summary_data: SummaryData) -> str:

    target_basho = BashoData(basho_id)
    next_basho = BashoData(get_next_basho(basho_id))
    out = ""
    # Header
    out += f"The {target_basho.year} {target_basho.month_name_full} {target_basho.name} Summary\n"
    out += f"   {target_basho.start_date_str} - {target_basho.end_date_str}\n"
    out += f"   {target_basho.city}, Japan\n"
    out += f"   {target_basho.venue_name}\n\n"

    # Yusho Winners
    out += "🏆 YUSHO WINNERS 🏆\n"
    if summary_data.yusho:
        for y in summary_data.yusho:
            rank = str(y.get('type')).ljust(10)
            out += f"{rank}: {y.get('shikonaEn')}\n"
    else:
        out += "None\n"
    out += "\n"

    # Special Prizes
    out += "🎌 SPECIAL PRIZES 🎌\n"
    if summary_data.special_prizes:
        for p in summary_data.special_prizes:
            prize_type = str(p.get('type')).ljust(10)
            out += f"{prize_type}: {p.get('shikonaEn')}\n"
    else:
        out += "None\n"
    out += "\n"

    # Next Tournament
    out += "📅 NEXT TOURNAMENT 📅\n"
    out += f"   {next_basho.name} \n"
    out += f"   {next_basho.start_date_str} — {next_basho.end_date_str}  \n"
    out += f"   {next_basho.city}, Japan\n"
    out += f"   {next_basho.venue_name}\n"

    return out


def generate_summary(target_basho_id: str):
    client = SumoAPIClient()

    prior_basho_id = get_previous_basho(target_basho_id)

    # torikumi_data = client.get_torikumi(target_basho_id)
    prior_torikumi = client.get_torikumi(prior_basho_id, day=15)

    basho = BashoData(target_basho_id)
    summary = SummaryData(prior_torikumi)

    content = build_summary_text(prior_basho_id, summary)
    title = "TOURNAMENT SUMMARY"

    payload = {
        "username": "Sumo-hooks",
        "avatar_url": "",
        "content": "Sumo update",
        "embeds": [
            {
                "author": {
                    "name": f" SUMMARY",
                    "url": "https://www3.nhk.or.jp/nhkworld/en/tv/sumo/",
                    "icon_url": "",
                },
                "title": title,
                "url": "https://www3.nhk.or.jp/nhkworld/en/tv/sumo/",
                "description": f"```\n{content}```",
                "color": basho.color,
                "fields": [],
                "thumbnail": {"url": ""},
                "image": {
                    "url": basho.venue_img,
                },
                "footer": {
                    "text": basho.venue_name,
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
    # We will just print to console, unless a specific flag is passed down the line.
    
    b = get_current_basho_id()
    payload = generate_summary(b)
    
    # We leave post_webhook available here, if desired, but we won't call it blindly to avoid testing with proper endpoints.
    if len(sys.argv) > 1 and sys.argv[1] == "--post":
        endpoints = os.getenv("testpoint", "").split(",")
        post_webhook(payload, endpoints)
    else:
        print("Run with '--post' to actually post to webhooks.")
