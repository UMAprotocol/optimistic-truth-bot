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
    "White Sox": "p2",
    "Astros": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, team1, team2):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy endpoint
        try:
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
                   (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    """ Determine the market resolution based on game data """
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return "recommendation: " + RESOLUTION_MAP[winner]
    elif game['Status'] == 'Canceled':
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == 'Postponed':
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-12"
    home_team = "White Sox"
    away_team = "Astros"

    # Fetch game data
    game_info = get_game_data(game_date, home_team, away_team)

    # Resolve the market based on the game data
    result = resolve_market(game_info)
    print(result)