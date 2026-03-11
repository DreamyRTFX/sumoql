"""
sumo_hooks.py — I/O concerns only: API client and webhook posting.
"""

import requests
from typing import Dict, List, Any

from sumo_data import HONBASHO_DATA


class SumoAPIClient:
    BASE_URL = "https://www.sumo-api.com/api"
    HONBASHO_DATA = HONBASHO_DATA  # Keep the class-level reference for backward compat

    def get_torikumi(self, basho_id: str, day: int = 1, division: str = "Makuuchi") -> Dict[str, Any]:
        r = requests.get(f"{self.BASE_URL}/basho/{basho_id}/torikumi/{division}/{day}")
        r.raise_for_status()
        return r.json()

    def get_banzuke(self, basho_id: str, division: str = "Makuuchi") -> Dict[str, Any]:
        r = requests.get(f"{self.BASE_URL}/basho/{basho_id}/banzuke/{division}")
        r.raise_for_status()
        return r.json()

    def get_basho_start_date(self, basho_id: str) -> str:
        """Fetches the start date for a given basho_id by querying Day 1 torikumi."""
        data = self.get_torikumi(basho_id, day=1)
        return data.get("startDate")

    def get_h2h(self, rikishi_id: int, opponent_id: int) -> Dict[str, Any]:
        r = requests.get(f"{self.BASE_URL}/rikishi/{rikishi_id}/matches/{opponent_id}")
        r.raise_for_status()
        return r.json()


def post_webhook(payload: Dict[str, Any], endpoints: List[str]):
    for ep in endpoints:
        if not ep:
            continue
        try:
            post = requests.post(url=ep, json=payload)
            post.raise_for_status()
        except Exception as e:
            print(f"Failed to post to {ep}: {e}")
