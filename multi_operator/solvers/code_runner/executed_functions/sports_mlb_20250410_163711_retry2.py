import os
import requests
from datetime import datetime
from python_dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
SPORTS_DATA_IO_NHL_API_KEY = os.getenv('SPORTS_DATA_IO_NHL_API_KEY')
NHL_API_URL = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
HEADERS = {'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_NHL_API_KEY}
RESOLUTION_MAP = {
    "Flames": "p2",
    "Ducks": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def fetch_nhl_game_results(date):
    response = requests.get(NHL_API_URL + date, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(game_date, home_team, away_team):
    games = fetch_nhl_game_results(game_date)
    if games is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP[home_team]
                elif game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP[away_team]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Set the game date and teams
game_date = "2025-04-09"
home_team = "Flames"
away_team = "Ducks"

# Resolve the market based on the game results
recommendation = resolve_market(game_date, home_team, away_team)
print(recommendation)