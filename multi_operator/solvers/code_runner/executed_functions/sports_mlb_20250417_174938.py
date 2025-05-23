import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError("SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. Please add it to your .env file.")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Mumbai Indians": "p2",  # Mumbai Indians win maps to p2
    "Sunrisers Hyderabad": "p1",  # Sunrisers Hyderabad win maps to p1
    "50-50": "p3",  # Tie or undetermined maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_game_data():
    """
    Fetches game data for the specified IPL game.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-17"
    team1_name = "Mumbai Indians"
    team2_name = "Sunrisers Hyderabad"
    
    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/mlb/stats/json/BoxScoresFinal/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            game_info = game_data.get("Game", {})
            home_team = game_info.get("HomeTeam")
            away_team = game_info.get("AwayTeam")
            
            # Check if either team matches our search
            if (home_team == team1_name and away_team == team2_name) or (home_team == team2_name and away_team == team1_name):
                return game_data

        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the BoxScoresFinal endpoint

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return "p4"  # No game data available, too early to resolve

    # Extract game info from the nested structure
    game_info = game.get("Game", {})
    status = game_info.get("Status")
    home_score = game_info.get("HomeTeamRuns")
    away_score = game_info.get("AwayTeamRuns")
    home_team = game_info.get("HomeTeam")
    away_team = game_info.get("AwayTeam")

    if status in ["Scheduled", "Delayed", "InProgress", "Suspended"]:
        return "p4"  # Game is not complete
    elif status == "Postponed":
        return "p4"  # Game postponed, market remains open
    elif status == "Canceled":
        return "p3"  # Game canceled, resolve as 50-50
    elif status == "Final":
        if home_score > away_score:
            return RESOLUTION_MAP[home_team]  # Home team won
        elif away_score > home_score:
            return RESOLUTION_MAP[away_team]  # Away team won
        else:
            return "p3"  # Tie, resolve as 50-50

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to query IPL game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()