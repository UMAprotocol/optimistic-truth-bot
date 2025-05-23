import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "GT": "p2",  # Gujarat Titans
    "DC": "p1",  # Delhi Capitals
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified IPL game.
    """
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-19"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == "GT" and game['AwayTeam'] == "DC" or game['HomeTeam'] == "DC" and game['AwayTeam'] == "GT":
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # Too early to resolve

    status = game.get("Status")
    if status == "Final":
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamScore")
        away_score = game.get("AwayTeamScore")
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        return RESOLUTION_MAP.get(winner, "p3")
    elif status in ["Canceled", "Postponed"]:
        return "p3"
    else:
        return "p4"

def main():
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()