import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# ─────────── generic GET wrapper ───────────
def _get(url, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code == 429:
                wait = backoff * 2**i
                time.sleep(wait)
                continue
            response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                return None

# ─────────── helpers ───────────
def fetch_match_result():
    data = _get(HLTV_EVENT_URL)
    if not data:
        return "p4"  # Unable to fetch data

    # Simulated logic to find the match and determine the outcome
    # This part should be replaced with actual logic to parse the HLTV event page
    # For demonstration, let's assume B8 won
    match_result = "B8"  # This should be dynamically determined from the fetched data

    return match_result

# ─────────── main ───────────
if __name__ == "__main__":
    result = fetch_match_result()
    if result == "B8":
        print("recommendation: p2")
    elif result == "Lynn Vision":
        print("recommendation: p1")
    else:
        print("recommendation: p3")