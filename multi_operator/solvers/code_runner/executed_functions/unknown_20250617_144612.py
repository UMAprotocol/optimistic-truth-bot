import os
import requests
from datetime import datetime, timedelta
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
            if response.status_code == 429:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data from {url}: {e}")
            continue
    return None

# ─────────── helpers ───────────
def fetch_match_result():
    today = datetime.utcnow()
    match_date = datetime(2025, 6, 17, 11, 0)  # UTC time for 7:00 AM ET
    if today < match_date:
        return "p4"  # Match has not yet occurred
    elif today > datetime(2025, 6, 24, 23, 59):
        return "p3"  # Match delayed beyond June 24, 2025

    # URL and tag for fetching match data
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-JUN-17"
    tag = "MatchResult"
    data = _get(url, tag)

    if not data:
        return "p3"  # No data could mean canceled or issues with the data source

    # Assuming data structure contains team names and status
    for game in data:
        if "Ugo Humbert" in game['Teams'] and "Denis Shapovalov" in game['Teams']:
            if game['Status'] == 'Final':
                winner = game['Winner']
                if winner == "Ugo Humbert":
                    return "p2"
                elif winner == "Denis Shapovalov":
                    return "p1"
            else:
                return "p3"  # Non-final status treated as canceled/delayed

    return "p3"  # Default to canceled/delayed if no matching game found

# ─────────── main ───────────
if __name__ == "__main__":
    result = fetch_match_result()
    print("recommendation:", result)