import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Blue Jays": "p1",
    "Orioles": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

logger = logging.getLogger(__name__)

def fetch_game_data(date, home_team, away_team):
    logger.info(f"Fetching game data for {away_team} @ {home_team} on {date}")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url)
        if response.status_code == 404:
            logger.warning("No data found for the specified date.")
            return None
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return game
        logger.warning("No matching game found.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status in ["Scheduled", "Delayed"]:
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Final", "Completed"]:
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score == away_score:
            return RESOLUTION_MAP["50-50"]
        elif home_score > away_score:
            return RESOLUTION_MAP["Blue Jays"]
        else:
            return RESOLUTION_MAP["Orioles"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    elif status == "Suspended":
        current_time = datetime.utcnow()
        deadline = datetime(2025, 4, 2, 3, 59, 59)
        if current_time <= deadline:
            return RESOLUTION_MAP["Too early to resolve"]
        else:
            return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-03-30"
    home_team = "TOR"
    away_team = "BAL"

    game = fetch_game_data(date, home_team, away_team)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()