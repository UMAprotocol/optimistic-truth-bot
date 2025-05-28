import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
ROLAND_GARROS_URL = "https://www.rolandgarros.com/fr-fr/"

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code in {401, 403, 404, 429}:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                return None

# ─────────── helpers ───────────
def check_player_progress(player_name):
    try:
        data = _get(ROLAND_GARROS_URL, "RolandGarrosData")
        if data:
            players = data.get('players', [])
            for player in players:
                if player.get('name') == player_name:
                    return player.get('stage', 'unknown')
        return 'unknown'
    except Exception as e:
        return 'unknown'

# ─────────── main ───────────
if __name__ == "__main__":
    player_name = "Grigor Dimitrov"
    current_stage = check_player_progress(player_name)
    if current_stage == 'quarterfinals':
        recommendation = 'p2'  # Yes, reached the quarterfinals
    elif current_stage == 'unknown':
        recommendation = 'p3'  # Unknown/50-50
    else:
        recommendation = 'p1'  # No, did not reach the quarterfinals

    print("recommendation:", recommendation)