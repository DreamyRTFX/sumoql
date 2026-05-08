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
    BashoData,
    SummaryData,
)


def build_summary_text(basho_data: BashoData, summary_data: SummaryData) -> str:
    out = ""
    # Header logic
    prior_label = basho_data.prior_basho_label.strip("()").upper()
    out += f"🌸 {prior_label} SUMMARY\n\n"

    # Yusho Winners
    out += "**YUSHO WINNERS**\n"
    if summary_data.yusho:
        for y in summary_data.yusho:
            rank = str(y.get('type')).ljust(10)
            out += f"{rank}: {y.get('shikonaEn')}\n"
    else:
        out += "None\n"
    out += "\n"

    # Special Prizes
    out += "**SPECIAL PRIZES**\n"
    if summary_data.special_prizes:
        for p in summary_data.special_prizes:
            prize_type = str(p.get('type')).ljust(10)
            out += f"{prize_type}: {p.get('shikonaEn')}\n"
    else:
        out += "None\n"
    out += "\n"

    # Next Tournament Logistics
    out += "**NEXT TOURNAMENT**\n"
    out += f"The {basho_data.name} begins {basho_data.start_date_str}.\n"
    out += f"Dates: {basho_data.start_date_str} — {basho_data.end_date_str} (JST) \n"
    out += f"Venue: {basho_data.venue_name}\n"

    return out


def generate_summary(target_basho_id: str):
    client = SumoAPIClient()

    prior_basho_id = get_previous_basho(target_basho_id)

    torikumi_data = client.get_torikumi(target_basho_id)
    prior_torikumi = client.get_torikumi(prior_basho_id, day=15)

    basho = BashoData(torikumi_data)
    summary = SummaryData(prior_torikumi)

    content = build_summary_text(basho, summary)
    title = "TOURNAMENT SUMMARY"

    prior_label = basho.prior_basho_label.strip("()").upper()

    payload = {
        "username": "Sumo-hooks",
        "avatar_url": "",
        "content": "Sumo update",
        "embeds": [
            {
                "author": {
                    "name": f"{prior_label} SUMMARY",
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
    # Respect user request: "do not use endpoints from .env for testing"
    # We will just print to console, unless a specific flag is passed down the line.
    
    payload = generate_summary("202603")
    
    # We leave post_webhook available here, if desired, but we won't call it blindly to avoid testing with proper endpoints.
    if len(sys.argv) > 1 and sys.argv[1] == "--post":
        endpoints = os.getenv("testpoint", "").split(",")
        post_webhook(payload, endpoints)
    else:
        print("Run with '--post' to actually post to webhooks.")
