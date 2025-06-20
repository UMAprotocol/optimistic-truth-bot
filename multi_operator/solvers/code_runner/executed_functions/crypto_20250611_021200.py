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

def fetch_game_data(game_date, home_team, away_team):
    """
    Fetches game data from the NBA API for a specific game date and teams.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    params = {
        "date": game_date
    }
    try:
        response = requests.get(f"{NBA_API_URL}/stats/json/GamesByDate/{game_date}", headers=headers, params=params)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game['GameId']
    except requests.RequestException as e:
        print(f"Failed to fetch game data: {str(e)}")
        return None

def fetch_player_stats(game_id, player_name):
    """
    Fetches player stats for a specific game and player.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    try:
        response = requests.get(f"{NBA_API_URL}/stats/json/PlayerGameStatsByGame/{game_id}", headers=headers)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat['FieldGoalsAttempted'], stat['FieldGoalsMade']
    except requests.RequestException as e:
        print(f"Failed to fetch player stats: {str(e)}")
        return None, None

def main():
    game_date = "2025-06-10"
    home_team = "CHI"
    away_team = "NY"
    player_name = "Angel Reese"

    game_id = fetch_game_data(game_date, home_team, away_team)
    if game_id:
        field_goals_attempted, field_goals_made = fetch_player_stats(game_id, player_name)
        if field_goals_attempted is not None and field_goals_attempted > 0:
            if field_goals_made == 0:
                print("recommendation: p2")  # Missed first shot
            else:
                print("recommendation: p1")  # Made first shot
        else:
            print("recommendation: p1")  # No field goal attempts or data unavailable
    else:
        print("recommendation: p1")  # Game data not found or game did not occur

if __name__ == "__main__":
    main()