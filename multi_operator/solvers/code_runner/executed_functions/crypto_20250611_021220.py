import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# API endpoints
NBA_API_URL = "https://api.sportsdata.io/v3/nba"

# Constants for the game and player in question
GAME_DATE = "2025-06-10"
GAME_TIME = "20:00:00"
PLAYER_NAME = "Angel Reese"
TEAM_A = "Chicago Sky"
TEAM_B = "New York Liberty"

def fetch_game_data():
    """
    Fetches game data from the NBA API for the specified game and player.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    # Construct the date in the required format
    game_datetime = f"{GAME_DATE}T{GAME_TIME}Z"
    try:
        # Fetch games on the specified date
        response = requests.get(
            f"{NBA_API_URL}/scoreboard/{GAME_DATE}",
            headers=headers
        )
        response.raise_for_status()
        games = response.json()

        # Find the game involving the specified teams
        for game in games:
            if (game['HomeTeam'] == TEAM_A and game['AwayTeam'] == TEAM_B) or \
               (game['HomeTeam'] == TEAM_B and game['AwayTeam'] == TEAM_A):
                game_id = game['GameID']
                # Fetch player game stats
                player_stats_response = requests.get(
                    f"{NBA_API_URL}/playergamelogs/{game_id}",
                    headers=headers
                )
                player_stats_response.raise_for_status()
                player_stats = player_stats_response.json()

                # Check player stats
                for stat in player_stats:
                    if stat['Name'] == PLAYER_NAME:
                        # Check the first field goal attempt
                        if stat['FieldGoalsAttempted'] > 0:
                            if stat['FieldGoalsMade'] < 1:
                                return "p2"  # Missed first shot
                            else:
                                return "p1"  # Made first shot
                return "p1"  # No field goal attempts or did not play
        return "p1"  # Game not found or cancelled
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return "p4"  # Unable to fetch data

def main():
    """
    Main function to determine the outcome of the market based on the player's performance.
    """
    result = fetch_game_data()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()