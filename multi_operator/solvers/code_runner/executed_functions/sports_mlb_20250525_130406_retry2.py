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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Yankees": "p2",
    "Rockies": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # Fallback to proxy endpoint
        url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

def analyze_game_data(games):
    """ Analyze game data to determine the outcome """
    for game in games:
        if game['HomeTeam'] == 'COL' and game['AwayTeam'] == 'NYY':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP['Rockies']
                elif away_score > home_score:
                    return RESOLUTION_MAP['Yankees']
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP['50-50']
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP['Too early to resolve']
    return RESOLUTION_MAP['Too early to resolve']

def main():
    game_date = "2025-05-24"
    games = get_game_data(game_date)
    result = analyze_game_data(games)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()