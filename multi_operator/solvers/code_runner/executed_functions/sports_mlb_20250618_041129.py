import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-06-17"
HOME_TEAM = "Mariners"
AWAY_TEAM = "Red Sox"

# Resolution map
RESOLUTION_MAP = {
    "Mariners": "p1",
    "Red Sox": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(games, home_team, away_team):
    """Resolve the market based on game outcome."""
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[home_team]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[away_team]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        result = resolve_market(games, HOME_TEAM, AWAY_TEAM)
    else:
        result = "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    print(result)