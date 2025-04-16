import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "HOU": "p2",  # Houston Astros win maps to p2
    "STL": "p1",  # St. Louis Cardinals win maps to p1
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

def get_team_abbreviation_map():
    """
    Fetches MLB team data and builds a mapping from full team names to API abbreviations.
    
    Returns:
        Dictionary mapping full team names to API abbreviations
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/teams?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        teams = response.json()
        return {f"{team['City']} {team['Name']}": team['Key'] for team in teams}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch team abbreviations: {e}")
        return {}

def fetch_game_data(date, team1_api, team2_api):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_api: First team abbreviation
        team2_api: Second team abbreviation

    Returns:
        Game data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1_api and game['AwayTeam'] == team2_api) or (game['HomeTeam'] == team2_api and game['AwayTeam'] == team1_api):
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
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
    if status in ["Final"]:
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP[home_team]
        elif away_score > home_score:
            return RESOLUTION_MAP[away_team]
    elif status in ["Canceled", "Postponed"]:
        return "p3"
    return "p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-15"
    team1_name = "Houston Astros"
    team2_name = "St. Louis Cardinals"
    
    team_abbreviation_map = get_team_abbreviation_map()
    if not team_abbreviation_map:
        print("recommendation: p4")
        return
    
    team1_api = team_abbreviation_map.get(team1_name)
    team2_api = team_abbreviation_map.get(team2_name)
    
    game = fetch_game_data(date, team1_api, team2_api)
    resolution = determine_resolution(game)
    
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()