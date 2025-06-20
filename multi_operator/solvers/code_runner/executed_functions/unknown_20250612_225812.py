"""
BLAST.tv Austin Major: MOUZ vs. FaZe resolver
p1 = FaZe
p2 = MOUZ
p3 = 50-50 (tie, canceled, or delayed)
"""
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── helper functions ───────────
def get_match_result():
    url = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        for match in data.get('matches', []):
            if match['team1'] == 'MOUZ' and match['team2'] == 'FaZe':
                if match['status'] == 'finished':
                    winner = match['winner']
                    if winner == 'MOUZ':
                        return 'p2'
                    elif winner == 'FaZe':
                        return 'p1'
                elif match['status'] in ['canceled', 'postponed']:
                    return 'p3'
        # If no specific match info is found, assume it's still upcoming
        return 'p3'
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return 'p3'

# ─────────── main execution ───────────
if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")