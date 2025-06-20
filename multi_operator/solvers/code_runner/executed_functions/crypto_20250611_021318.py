import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# API endpoint configuration
NBA_API_URL = "https://api.sportsdata.io/v3/nba"

def fetch_game_data(game_date, teams):
    """
    Fetches game data for a specific date and teams from the NBA API.
    
    Args:
        game_date (str): Date of the game in YYYY-MM-DD format.
        teams (tuple): Tuple containing the home and away team names.
    
    Returns:
        dict: JSON response containing game data.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    params = {
        "date": game_date
    }
    try:
        response = requests.get(f"{NBA_API_URL}/scoreboard/{game_date}", headers=headers, params=params)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == teams[0] and game['AwayTeam'] == teams[1]:
                return game
    except requests.RequestException as e:
        print(f"Failed to fetch game data: {e}")
    return None

def check_first_shot(game_id, player_name):
    """
    Checks whether the specified player missed their first field goal attempt in the game.
    
    Args:
        game_id (int): ID of the game.
        player_name (str): Name of the player.
    
    Returns:
        str: 'p1' if the player made the first shot, 'p2' if missed, 'p4' if data is unavailable.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    try:
        response = requests.get(f"{NBA_API_URL}/stats/{game_id}/PlayerGameStatsByPlayer", headers=headers)
        response.raise_for_status()
        stats = response.json()
        for stat in stats:
            if stat['Name'] == player_name:
                attempts = stat['FieldGoalsAttempted']
                made = stat['FieldGoalsMade']
                if attempts > 0:
                    return 'p2' if made == 0 else 'p1'
    except requests.RequestException as e:
        print(f"Failed to fetch player stats: {e}")
    return 'p4'

def main():
    game_date = "2025-06-10"
    teams = ("CHI", "NYL")  # Chicago Sky and New York Liberty
    player_name = "Angel Reese"
    
    game_data = fetch_game_data(game_date, teams)
    if game_data:
        game_id = game_data['GameID']
        result = check_first_shot(game_id, player_name)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()