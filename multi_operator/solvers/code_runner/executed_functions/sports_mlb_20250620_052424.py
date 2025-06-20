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
    "Padres": "p2",
    "Dodgers": "p1",
    "Canceled": "p3",
    "Postponed": "p4",
    "Unknown": "p4"
}

def get_game_data(date, team1, team2):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to proxy if primary fails
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}", headers=HEADERS, timeout=10)
        games = response.json()

        # Find the game between the specified teams
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return "recommendation: " + RESOLUTION_MAP.get(winner, "Unknown")
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-19"
    home_team = "Dodgers"
    away_team = "Padres"

    # Fetch game data and resolve the market
    game_info = get_game_data(game_date, home_team, away_team)
    result = resolve_market(game_info)
    print(result)