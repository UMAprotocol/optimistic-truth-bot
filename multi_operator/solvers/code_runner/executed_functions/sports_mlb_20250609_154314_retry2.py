import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Braves": "p2",
    "Giants": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
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
        if game['AwayTeam'] == 'ATL' and game['HomeTeam'] == 'SF':
            if game['Status'] == 'Final':
                if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP['Braves']
                elif game['AwayTeamRuns'] < game['HomeTeamRuns']:
                    return RESOLUTION_MAP['Giants']
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP['Postponed']
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP['Canceled']
    return RESOLUTION_MAP['Unknown']

def main():
    game_date = "2025-06-08"
    games = get_game_data(game_date)
    result = analyze_game_data(games)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()