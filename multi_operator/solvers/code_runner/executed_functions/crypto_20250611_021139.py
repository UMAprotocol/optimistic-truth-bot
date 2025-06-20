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

def fetch_game_data(game_date, team1, team2):
    """
    Fetches game data for a specific NBA game.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    params = {
        "date": game_date
    }
    try:
        response = requests.get(f"{NBA_API_URL}/scores/json/GamesByDate/{game_date}", headers=headers, params=params)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if team1 in game['HomeTeam'] and team2 in game['AwayTeam']:
                return game['GameId']
    except requests.RequestException as e:
        print(f"Failed to fetch game data: {e}")
        return None

def fetch_player_stats(game_id, player_name):
    """
    Fetches player stats for a specific game.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    try:
        response = requests.get(f"{NBA_API_URL}/stats/json/PlayerGameStatsByGame/{game_id}", headers=headers)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if player_name in stat['Name']:
                return stat
    except requests.RequestException as e:
        print(f"Failed to fetch player stats: {e}")
        return None

def main():
    game_date = "2025-06-10"
    team1 = "CHI"  # Chicago Sky
    team2 = "NYL"  # New York Liberty
    player_name = "Angel Reese"

    game_id = fetch_game_data(game_date, team1, team2)
    if game_id:
        player_stat = fetch_player_stats(game_id, player_name)
        if player_stat:
            field_goals_attempted = player_stat['FieldGoalsAttempted']
            if field_goals_attempted > 0:
                first_shot_made = player_stat['FieldGoalsMade'] > 0
                if first_shot_made:
                    print("recommendation: p1")  # She made her first shot
                else:
                    print("recommendation: p2")  # She missed her first shot
            else:
                print("recommendation: p1")  # No field goal attempts, resolve to "No"
        else:
            print("recommendation: p1")  # Player did not play or no stats available
    else:
        print("recommendation: p1")  # Game not found or did not occur

if __name__ == "__main__":
    main()