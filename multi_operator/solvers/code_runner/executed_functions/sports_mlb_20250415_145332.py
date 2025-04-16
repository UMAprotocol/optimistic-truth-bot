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
    "TOR": "p1",  # Toronto Blue Jays maps to p1
    "ATL": "p2",  # Atlanta Braves maps to p2
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

def fetch_game_data(date, team1_name, team2_name, team_abbreviation_map=None):
    """
    Fetches game data for the specified date and teams.
    """
    if team_abbreviation_map is None:
        team_abbreviation_map = get_team_abbreviation_map()
    
    team1_api = team_abbreviation_map.get(team1_name, team1_name)
    team2_api = team_abbreviation_map.get(team2_name, team2_name)

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
    """
    if not game:
        return "p4"

    status = game.get("Status")
    if status in ["Scheduled", "InProgress", "Delayed", "Suspended"]:
        return "p4"
    elif status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP[game["HomeTeam"]]
        elif away_score > home_score:
            return RESOLUTION_MAP[game["AwayTeam"]]
        else:
            return "p3"
    elif status in ["Postponed", "Canceled"]:
        return "p3"
    else:
        return "p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-14"
    team1_name = "Toronto Blue Jays"
    team2_name = "Atlanta Braves"
    
    team_abbreviation_map = get_team_abbreviation_map()
    if not team_abbreviation_map:
        print("recommendation: p4")
        return
    
    game = fetch_game_data(date, team1_name, team2_name, team_abbreviation_map)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()