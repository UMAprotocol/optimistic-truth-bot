import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "IND": "p2",  # Indiana Pacers
    "OKC": "p1",  # Oklahoma City Thunder
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date):
    """
    Fetches game data for the specified date.
    """
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
    """
    Resolves the market based on the game outcome.
    """
    for game in games:
        if game['HomeTeam'] == 'IND' or game['AwayTeam'] == 'IND':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return "recommendation: " + RESOLUTION_MAP[winner]
            elif game['Status'] in ['Postponed', 'Canceled']:
                return "recommendation: " + RESOLUTION_MAP[game['Status']]
    return "recommendation: p4"  # If no relevant game is found or in progress

if __name__ == "__main__":
    # Define the date of the game
    game_date = "2025-06-16"
    games = get_game_data(game_date)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print("recommendation: p4")  # Unable to fetch data