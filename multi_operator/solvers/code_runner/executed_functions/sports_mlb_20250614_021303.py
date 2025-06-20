import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API access
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Yankees": "p2",
    "Red Sox": "p1",
    "50-50": "p3"
}

def get_game_data(date, team1, team2):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to proxy if primary fails
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
    return None

def resolve_market(game):
    """ Determine the market resolution based on game data """
    if not game:
        return "recommendation: p4"  # No data available
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game['Status'] == 'Canceled':
        return "recommendation: p3"
    elif game['Status'] == 'Postponed':
        return "recommendation: p4"  # Market remains open
    return "recommendation: p4"

if __name__ == "__main__":
    # Set the game date and teams involved
    game_date = "2025-06-13"
    home_team = "Red Sox"
    away_team = "Yankees"

    # Fetch game data
    game_info = get_game_data(game_date, home_team, away_team)

    # Resolve the market based on the game data
    result = resolve_market(game_info)
    print(result)