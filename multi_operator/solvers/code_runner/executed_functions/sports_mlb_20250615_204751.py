import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Twins": "p2",
    "Astros": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p4"
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

def resolve_market(games):
    """ Resolve the market based on game data """
    for game in games:
        if game['HomeTeam'] == 'HOU' and game['AwayTeam'] == 'MIN':
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP["Astros"]
                else:
                    return RESOLUTION_MAP["Twins"]
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP["Canceled"]
    return RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    # Set the date of the game
    game_date = "2025-06-15"
    try:
        games = get_game_data(game_date)
        recommendation = resolve_market(games)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")