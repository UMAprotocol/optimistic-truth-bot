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
    "Royals": "p2",
    "Cardinals": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p4"
}

def get_game_data(date, home_team, away_team):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to proxy if primary fails
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}", timeout=10)
        games = response.json()

        # Find the specific game
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game['Status'] == "Final":
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return "recommendation: " + RESOLUTION_MAP[game['HomeTeam']]
        else:
            return "recommendation: " + RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-05"
    home_team = "Cardinals"
    away_team = "Royals"

    # Fetch game data and resolve the market
    game_info = get_game_data(game_date, home_team, away_team)
    result = resolve_market(game_info)
    print(result)