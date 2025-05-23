import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Royal Challengers Bangalore": "p2",
    "Rajasthan Royals": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified IPL game.
    
    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-24"
    team1_name = "Royal Challengers Bangalore"
    team2_name = "Rajasthan Royals"
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == team1_name and game['AwayTeamName'] == team2_name:
                return game
            elif game['HomeTeamName'] == team2_name and game['AwayTeamName'] == team1_name:
                return game

        logging.info("No matching game found.")
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return "p4"

    status = game.get("Status")
    if status == "Final":
        home_score = game.get("HomeTeamScore")
        away_score = game.get("AwayTeamScore")
        if home_score > away_score:
            return RESOLUTION_MAP[game["HomeTeamName"]]
        else:
            return RESOLUTION_MAP[game["AwayTeamName"]]
    elif status == "Canceled":
        return "p3"
    elif status == "Postponed":
        return "p4"
    else:
        return "p4"

def main():
    """
    Main function to determine the resolution of the IPL game.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()