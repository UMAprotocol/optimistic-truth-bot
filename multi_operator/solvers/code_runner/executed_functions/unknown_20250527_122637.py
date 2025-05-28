import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
FRENCH_OPEN_URL = "https://www.rolandgarros.com/fr-fr/"

# ─────────── generic GET wrapper ───────────
def _get(url, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code == 429:
                time.sleep(backoff * (2 ** i))
        except requests.RequestException as e:
            print(f"Request failed: {e}")
    return None

# ─────────── helpers ───────────
def check_player_progress(player_name):
    data = _get(FRENCH_OPEN_URL + "api/players")
    if data:
        for player in data:
            if player['name'] == player_name:
                return player['progress']
    return None

# ─────────── main ───────────
def main():
    player_name = "Grigor Dimitrov"
    current_date = datetime.utcnow().date()
    tournament_start_date = datetime.strptime("2025-05-25", "%Y-%m-%d").date()
    tournament_end_date = datetime.strptime("2025-06-08", "%Y-%m-%d").date()

    if current_date < tournament_start_date:
        print("recommendation: p4")  # Tournament has not started
    elif current_date > tournament_end_date:
        print("recommendation: p4")  # Tournament has ended, no data available
    else:
        progress = check_player_progress(player_name)
        if progress:
            if "Quarterfinals" in progress:
                print("recommendation: p2")  # Player reached the quarterfinals
            else:
                print("recommendation: p1")  # Player did not reach the quarterfinals
        else:
            print("recommendation: p4")  # Data unavailable or player not found

if __name__ == "__main__":
    main()