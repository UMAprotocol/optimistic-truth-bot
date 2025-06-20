import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for the API endpoint
NBA_API_URL = "https://api.sportsdata.io/v3/nba"

def fetch_game_data(game_date, home_team, away_team):
    """
    Fetches game data from the SportsDataIO NBA API.
    """
    url = f"{NBA_API_URL}/scores/json/GamesByDate/{game_date}"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
        logging.info("No matching game found.")
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
    return None

def check_angel_reese_first_shot(game_id):
    """
    Checks if Angel Reese missed her first field goal attempt in the specified game.
    """
    url = f"{NBA_API_URL}/stats/json/PlayerGameStatsByGame/{game_id}"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == "Angel Reese":
                # Assuming the API provides a list of shots, and the first one is the first attempt
                first_shot_made = stat['FieldGoalsMade'] > 0 and stat['FieldGoalAttempts'] == 1
                return not first_shot_made
        logging.info("Angel Reese did not play or did not attempt any field goals.")
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
    return False

def main():
    """
    Main function to determine if Angel Reese missed her first shot.
    """
    game_date = "2025-06-17"
    home_team = "WAS"  # Washington Mystics
    away_team = "CHI"  # Chicago Sky

    game = fetch_game_data(game_date, home_team, away_team)
    if game:
        missed_first_shot = check_angel_reese_first_shot(game['GameID'])
        if missed_first_shot:
            print("recommendation: p2")  # Yes, she missed
        else:
            print("recommendation: p1")  # No, she did not miss
    else:
        print("recommendation: p1")  # Resolve to "No" if game is not found or other conditions are met

if __name__ == "__main__":
    main()