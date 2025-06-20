import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-06-19"
HOME_TEAM = "Blue Jays"
AWAY_TEAM = "Diamondbacks"

# Resolution map
RESOLUTION_MAP = {
    "Blue Jays": "p1",
    "Diamondbacks": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_team_keys():
    """Retrieve MLB team keys."""
    url = "https://api.sportsdata.io/v3/mlb/scores/json/Teams"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {}
    teams = response.json()
    return {f"{team['City']} {team['Name']}": team["Key"] for team in teams}

def get_game_by_date(date, home_key, away_key):
    """Retrieve game details by date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None
    games = response.json()
    for game in games:
        if game["HomeTeam"] == home_key and game["AwayTeam"] == away_key:
            return game
    return None

def resolve_market(game):
    """Resolve the market based on game status and outcome."""
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        home_runs = game["HomeTeamRuns"]
        away_runs = game["AwayTeamRuns"]
        if home_runs > away_runs:
            return RESOLUTION_MAP[HOME_TEAM]
        elif away_runs > home_runs:
            return RESOLUTION_MAP[AWAY_TEAM]
    elif game["Status"] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game["Status"] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    team_keys = get_team_keys()
    home_key = team_keys.get(HOME_TEAM)
    away_key = team_keys.get(AWAY_TEAM)
    if not home_key or not away_key:
        print("Team keys not found.")
        return
    game = get_game_by_date(GAME_DATE, home_key, away_key)
    result = resolve_market(game)
    print("recommendation:", result)

if __name__ == "__main__":
    main()