import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# API endpoint for NBA data (Sports Data IO)
NBA_API_ENDPOINT = "https://api.sportsdata.io/v3/nba"

# Headers for API request
HEADERS = {
    "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
}

def fetch_game_data(game_date, team1, team2):
    """
    Fetches game data for a specific matchup on a given date.
    """
    url = f"{NBA_API_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    games = response.json()

    # Find the game between the specified teams
    for game in games:
        if (team1 in game['HomeTeam'] or team1 in game['AwayTeam']) and \
           (team2 in game['HomeTeam'] or team2 in game['AwayTeam']):
            return game
    return None

def check_player_shot(game_id, player_name):
    """
    Checks if the specified player missed their first field goal attempt in the game.
    """
    url = f"{NBA_API_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    player_stats = response.json()

    # Find the player stats
    for stat in player_stats:
        if player_name in stat['Name']:
            # Check the first field goal attempt result
            if stat['FieldGoalsAttempted'] > 0 and stat['FieldGoalsMade'] < stat['FieldGoalsAttempted']:
                return True  # Missed first shot
            break
    return False  # Made first shot or no attempts

def main():
    game_date = "2025-06-17"
    team1 = "CHI"  # Chicago Sky
    team2 = "WAS"  # Washington Mystics
    player_name = "Angel Reese"

    try:
        game = fetch_game_data(game_date, team1, team2)
        if game and game['Status'] == "Scheduled":
            game_id = game['GameID']
            missed_first_shot = check_player_shot(game_id, player_name)
            if missed_first_shot:
                print("recommendation: p2")  # Yes, missed first shot
            else:
                print("recommendation: p1")  # No, did not miss first shot
        else:
            print("recommendation: p1")  # Game not found or not scheduled, resolve to "No"
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()