import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Punjab": "p2",  # Punjab Kings win maps to p2
    "Rajasthan": "p1",  # Rajasthan Royals win maps to p1
    "50-50": "p3",  # Game not completed by deadline maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

def fetch_game_data():
    """
    Fetches game data for the IPL match between Punjab Kings and Rajasthan Royals on April 5, 2025.
    """
    date = "2025-04-05"
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == "Punjab Kings" and game['AwayTeamName'] == "Rajasthan Royals":
                return game
        return None

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
    home_team = game.get("HomeTeamName")
    away_team = game.get("AwayTeamName")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")

    if status == "Final":
        if home_score > away_score:
            return RESOLUTION_MAP[home_team]  # Home team wins
        elif away_score > home_score:
            return RESOLUTION_MAP[away_team]  # Away team wins
    elif status in ["Scheduled", "InProgress"]:
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        current_time = datetime.utcnow()
        deadline = datetime(2025, 4, 13, 3, 59, 59)  # April 12, 11:59 PM ET in UTC
        if current_time > deadline:
            return RESOLUTION_MAP["50-50"]
        else:
            return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()