import os
import requests
import re
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
            if response.status_code in (401, 403):
                raise Exception(f"Access denied or invalid API key used.")
            if response.status_code == 404:
                return None  # Not found
            if response.status_code == 429:
                time.sleep(backoff * (2 ** i))  # Exponential backoff
        except requests.RequestException as e:
            if i == retries - 1:
                raise Exception(f"API request failed after {retries} attempts: {str(e)}")
    return None

# ─────────── main ───────────
def check_speech_for_term(date_str, term):
    # Construct the URL for the speech video or transcript
    url = f"https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate/{date_str}"
    games = _get(url, "GamesByDate")
    if not games:
        return "p1"  # No games found, assuming no speech occurred

    # Check each game for the term
    for game in games:
        if term.lower() in game.get("Summary", "").lower():
            return "p2"  # Term found

    return "p1"  # Term not found

if __name__ == "__main__":
    EVENT_DATE = "2025-05-24"
    TERM_TO_FIND = "Beast"
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    if current_date > EVENT_DATE:
        recommendation = check_speech_for_term(EVENT_DATE, TERM_TO_FIND)
    else:
        recommendation = "p4"  # Event has not occurred yet

    print(f"recommendation: {recommendation}")