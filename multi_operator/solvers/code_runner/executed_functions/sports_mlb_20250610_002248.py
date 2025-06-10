import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"

# Game details
GAME_DATE = "2025-05-30"
HOME_TEAM = "Blue Jays"
AWAY_TEAM = "Athletics"

# Resolution map
RESOLUTION_MAP = {
    "Blue Jays": "p1",
    "Athletics": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_games_by_date(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled within the season
                new_date = game.get('Day', GAME_DATE)
                if new_date > GAME_DATE:
                    return RESOLUTION_MAP["Too early to resolve"]
                else:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_games_by_date(GAME_DATE)
    if games:
        recommendation = resolve_market(games)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", recommendation)