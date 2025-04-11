import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NHL_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Golden Knights": "p1",
    "Kraken": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

logger = logging.getLogger(__name__)

def fetch_game_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/BoxScoresFinal/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        games = response.json()

        for game_data in games:
            game_info = game_data.get("Game", {})
            home_team = game_info.get("HomeTeam")
            away_team = game_info.get("AwayTeam")
            
            if (home_team == team1 and away_team == team2) or (home_team == team2 and away_team == team1):
                game_data["team1"] = team1
                game_data["team2"] = team2
                return game_data

        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    game_info = game.get("Game", {})
    status = game_info.get("Status")
    home_score = game_info.get("HomeTeamScore")
    away_score = game_info.get("AwayTeamScore")
    home_team_name = game_info.get("HomeTeam")
    away_team_name = game_info.get("AwayTeam")
    
    team1 = game.get("team1")
    team2 = game.get("team2")

    if status in ["Scheduled", "Delayed", "InProgress", "Suspended"]:
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    elif status == "Final" or status == "F/OT" or status == "F/SO":
        if home_score == away_score:
            return RESOLUTION_MAP["50-50"]
        elif home_score > away_score:
            winning_team = home_team_name
        else:
            winning_team = away_team_name

        if winning_team == team1:
            return RESOLUTION_MAP[team1]
        else:
            return RESOLUTION_MAP[team2]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-10"
    team1 = "VGK"
    team2 = "SEA"

    game = fetch_game_data(date, team1, team2)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()