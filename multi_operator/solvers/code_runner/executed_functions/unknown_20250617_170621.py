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
            if response.status_code in (401, 403):
                print(f"Access denied or bad request at {url}")
                return None
            if response.status_code == 404:
                print(f"Resource not found at {url}")
                return None
            if response.status_code == 429:
                print(f"Rate limit exceeded, retrying in {backoff * (2 ** i)} seconds")
                time.sleep(backoff * (2 ** i))
        except requests.RequestException as e:
            print(f"Request failed: {e}")
    return None

# ─────────── main ───────────
def main():
    match_date = "2025-06-17"
    player1 = "Jordan Thompson"
    player2 = "Jaume Munar"
    tournament_url = "https://www.lta.org.uk/fan-zone/international/hsbc-championships/"

    # Fetch tournament data
    match_info = _get(tournament_url, "HSBC Championships")
    if match_info is None:
        print("Failed to retrieve match data.")
        return

    # Check match status and result
    for match in match_info:
        if (match['date'] == match_date and
            player1 in match['players'] and
            player2 in match['players']):
            if match['status'] == 'completed':
                winner = match['winner']
                if winner == player1:
                    print("recommendation: p2")  # Thompson wins
                elif winner == player2:
                    print("recommendation: p1")  # Munar wins
            elif match['status'] in ['canceled', 'postponed']:
                print("recommendation: p3")  # Match canceled or postponed
            return

    # If no match found or in progress
    print("recommendation: p3")  # Unknown or 50-50 if delayed beyond June 24, 2025

if __name__ == "__main__":
    main()