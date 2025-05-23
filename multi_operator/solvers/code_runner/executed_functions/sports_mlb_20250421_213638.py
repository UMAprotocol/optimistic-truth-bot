import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Kolkata Knight Riders": "p2",
    "Gujarat Titans": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_ipl_game_data():
    """
    Fetches IPL game data for Kolkata Knight Riders vs. Gujarat Titans on the specified date.
    """
    date = "2025-04-21"
    team1 = "Kolkata Knight Riders"
    team2 = "Gujarat Titans"
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == team1 and game['AwayTeamName'] == team2:
                return game
            elif game['HomeTeamName'] == team2 and game['AwayTeamName'] == team1:
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

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open
    elif game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            return RESOLUTION_MAP[game['HomeTeamName']]
        elif game['AwayTeamScore'] > game['HomeTeamScore']:
            return RESOLUTION_MAP[game['AwayTeamName']]
        else:
            return RESOLUTION_MAP["50-50"]
    else:
        return "p4"  # Game not completed yet

def main():
    """
    Main function to determine the resolution of the IPL game market.
    """
    game_data = fetch_ipl_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()