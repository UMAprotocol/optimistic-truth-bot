import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code == 429:
                time.sleep(backoff * (2 ** i))
        except requests.RequestException as e:
            print(f"Error during {tag}: {str(e)}")
    return None

# ─────────── main ───────────
def resolve_match():
    match_date = "2025-06-11"
    player1 = "Arthur Rinderknech"
    player2 = "Marton Fucsovics"
    tournament = "Boss Open"
    round_info = "second round"

    # Construct the URL for the API call
    url = f"https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate/{match_date}"
    games = _get(url, "GamesByDate")

    if not games:
        return "recommendation: p3"  # Assume unknown/50-50 if no data

    for game in games:
        if (tournament in game['Tournament'] and
            round_info in game['Round'] and
            player1 in game['Players'] and
            player2 in game['Players']):
            if game['Status'] == "Finished":
                winner = game['Winner']
                if winner == player1:
                    return "recommendation: p2"  # Rinderknech wins
                elif winner == player2:
                    return "recommendation: p1"  # Fucsovics wins
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "recommendation: p3"  # Match canceled or postponed

    return "recommendation: p3"  # Default to unknown/50-50 if no match found

if __name__ == "__main__":
    result = resolve_match()
    print(result)