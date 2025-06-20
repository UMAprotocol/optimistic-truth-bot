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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Orioles": "p2",
    "Rays": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    """ Fetch game data for a specific date """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games):
    """ Resolve the market based on game results """
    for game in games:
        if game['HomeTeam'] == 'BAL' and game['AwayTeam'] == 'TB':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP["Orioles"]
                elif away_score > home_score:
                    return "recommendation: " + RESOLUTION_MAP["Rays"]
            elif game['Status'] == 'Canceled':
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game['Status'] == 'Postponed':
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Define the date of the game
    game_date = "2025-06-16"
    games = get_game_data(game_date)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print("recommendation: " + RESOLUTION_MAP["Too early to resolve"])