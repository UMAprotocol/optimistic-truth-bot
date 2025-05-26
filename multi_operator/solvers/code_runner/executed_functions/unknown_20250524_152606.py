import os
import requests
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
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.ok:
                return r.json()
            if r.status_code in (401, 403):
                return None
            if r.status_code == 404:
                return []
            if r.status_code == 429:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            if i == retries - 1:
                raise e
            time.sleep(backoff * 2**i)
    return None

# ─────────── main ───────────
def main():
    event_date = "2025-05-24"
    term = "F-47"
    url = f"https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate/{event_date}"
    games = _get(url, "GamesByDate")

    if not games:
        print("recommendation: p1")  # No games found, assuming no mention of term
        return

    for game in games:
        if term in game.get("Summary", ""):
            print("recommendation: p2")  # Term found
            return

    print("recommendation: p1")  # Term not found in any game summaries

if __name__ == "__main__":
    main()