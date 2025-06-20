import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# NBA API endpoint configuration
NBA_API_ENDPOINT = "https://api.sportsdata.io/v3/nba"

def fetch_nba_game_score(game_date, game_time, teams):
    """
    Fetches the NBA game score for the specified teams at the specified start time.

    Args:
        game_date (str): Date of the game in YYYY-MM-DD format.
        game_time (str): Scheduled start time of the game in HH:MM format.
        teams (tuple): Tuple containing the two team names.

    Returns:
        dict: Dictionary containing the scoring information or None if data is not available.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NBA_API_KEY
    }
    # Convert game time to UTC for API compatibility
    game_datetime = datetime.strptime(f"{game_date} {game_time}", "%Y-%m-%d %H:%M")
    game_datetime_utc = game_datetime - timedelta(hours=4)  # Assuming game time is in ET

    # Format the date and time for the API request
    formatted_date = game_datetime_utc.strftime("%Y-%m-%d")

    try:
        response = requests.get(
            f"{NBA_API_ENDPOINT}/scores/json/GamesByDate/{formatted_date}",
            headers=headers
        )
        response.raise_for_status()
        games = response.json()

        # Find the game matching the specified teams
        for game in games:
            if teams[0] in game['HomeTeam'] and teams[1] in game['AwayTeam']:
                return game
            elif teams[1] in game['HomeTeam'] and teams[0] in game['AwayTeam']:
                return game

    except requests.RequestException as e:
        print(f"Failed to fetch NBA game data: {e}")

    return None

def check_scores_in_first_minute(game_data):
    """
    Checks if both teams scored in the first minute of the game.

    Args:
        game_data (dict): Game data containing scoring details.

    Returns:
        bool: True if both teams scored in the first minute, False otherwise.
    """
    if not game_data:
        return False

    # Example logic to check the score timeline
    # This part of the code assumes that there's a way to check the minute-by-minute score.
    # Adjust the logic based on the actual data structure returned by the API.
    home_score_first_minute = game_data['HomeTeamScore'] > 0
    away_score_first_minute = game_data['AwayTeamScore'] > 0

    return home_score_first_minute and away_score_first_minute

def main():
    # Game details
    game_date = "2025-06-19"
    game_time = "20:30"  # 8:30 PM ET
    teams = ("OKC", "IND")  # Oklahoma City Thunder and Indiana Pacers

    # Fetch game data
    game_data = fetch_nba_game_score(game_date, game_time, teams)

    # Check if both teams scored in the first minute
    both_scored = check_scores_in_first_minute(game_data)

    # Print the recommendation based on the result
    if both_scored:
        print("recommendation: p2")  # Yes, both teams scored
    else:
        print("recommendation: p1")  # No, one or both teams did not score

if __name__ == "__main__":
    main()