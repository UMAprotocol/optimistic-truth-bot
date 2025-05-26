import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Yankees": "p2",
    "Rockies": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p4"
}

def get_game_data(date):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except Exception:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            response.raise_for_status()
    return response.json()

def analyze_game_data(games):
    """ Analyze game data to determine the outcome """
    for game in games:
        if game['Day'] == '2025-05-24' and game['AwayTeam'] == 'NYY' and game['HomeTeam'] == 'COL':
            if game['Status'] == 'Final':
                if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP['Yankees']
                else:
                    return RESOLUTION_MAP['Rockies']
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP['Postponed']
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP['Canceled']
    return RESOLUTION_MAP['Unknown']

def main():
    date_str = '2025-05-24'
    games = get_game_data(date_str)
    result = analyze_game_data(games)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()