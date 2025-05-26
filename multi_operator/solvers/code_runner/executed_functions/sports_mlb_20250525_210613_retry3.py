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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Royals": "p2",
    "Twins": "p1",
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games):
    """ Resolve the market based on game results """
    for game in games:
        if game['HomeTeam'] == 'MIN' and game['AwayTeam'] == 'KC':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP["Twins"]
                else:
                    return "recommendation: " + RESOLUTION_MAP["Royals"]
            elif game['Status'] == 'Postponed':
                return "recommendation: " + RESOLUTION_MAP["Postponed"]
            elif game['Status'] == 'Canceled':
                return "recommendation: " + RESOLUTION_MAP["Canceled"]
    return "recommendation: p4"

if __name__ == "__main__":
    # Set the date of the game
    game_date = "2025-05-25"
    games = get_game_data(game_date)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print("recommendation: p4")