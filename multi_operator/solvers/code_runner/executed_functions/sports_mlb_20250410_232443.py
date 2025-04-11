import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Toronto Blue Jays": "p2",  # Toronto Blue Jays win maps to p2
    "Boston Red Sox": "p1",    # Boston Red Sox win maps to p1
    "50-50": "p3",             # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

def fetch_game_data():
    """
    Fetches game data for the specified date and teams.
    """
    date = "2025-04-10"
    home_team = "BOS"  # Boston Red Sox abbreviation
    away_team = "TOR"  # Toronto Blue Jays abbreviation
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return game
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP["Boston Red Sox"]
        else:
            return RESOLUTION_MAP["Toronto Blue Jays"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()