import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code in (401, 403, 404):
                continue
            if response.status_code == 429:
                time.sleep(backoff * 2**i)
        except requests.RequestException:
            continue
    return None

# ─────────── helpers ───────────
def get_game_result(date_str):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date_str}"
    games = _get(url, "GamesByDate")
    if games:
        for game in games:
            if game['HomeTeam'] == 'IND' and game['AwayTeam'] == 'OKC':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "p2"  # Pacers win
                    else:
                        return "p1"  # Thunder win
                elif game['Status'] == 'Postponed':
                    return "p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "p3"  # Game canceled
    return "p4"  # No data found or game not completed

# ─────────── main ───────────
if __name__ == "__main__":
    DATE = "2025-06-05"
    recommendation = get_game_result(DATE)
    print("recommendation:", recommendation)