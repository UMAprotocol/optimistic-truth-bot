import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
GAME_DATE = "2025-06-17"
GAME_TIME = "20:00:00"
TIMEZONE = "US/Eastern"
TEAM_A = "Chicago Sky"
TEAM_B = "Washington Mystics"
PLAYER_NAME = "Angel Reese"

# API Endpoints
WNBA_STATS_ENDPOINT = "https://api.sportsdata.io/v3/wnba/stats/json/PlayerGameStatsByDate"

def fetch_game_data(date):
    """
    Fetches game data for the specified date.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    response = requests.get(f"{WNBA_STATS_ENDPOINT}/{date}", headers=headers)
    response.raise_for_status()
    return response.json()

def analyze_player_shots(game_data, team_a, team_b, player_name):
    """
    Analyzes the player's shots to determine if the first field goal attempt was missed.
    """
    for game in game_data:
        if game['Team'] == team_a or game['Team'] == team_b:
            if game['Name'] == player_name:
                shots = game['FieldGoalsAttempted']
                if shots > 0:
                    made_shots = game['FieldGoalsMade']
                    # Check if the first shot was missed
                    if made_shots < shots:
                        return "p2"  # Missed first shot
                    else:
                        return "p1"  # Made first shot
    return "p4"  # No data or did not play

def main():
    """
    Main function to process the WNBA game data and determine the outcome.
    """
    try:
        # Convert game date and time to UTC for consistency
        game_datetime = datetime.strptime(f"{GAME_DATE} {GAME_TIME}", "%Y-%m-%d %H:%M:%S")
        game_data = fetch_game_data(GAME_DATE)
        result = analyze_player_shots(game_data, TEAM_A, TEAM_B, PLAYER_NAME)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")  # Default to unresolved if there's an error

if __name__ == "__main__":
    main()