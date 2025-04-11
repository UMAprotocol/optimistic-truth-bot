import os
import requests
import re
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

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "TOR": "p1",  # Blue Jays (Home team) maps to p1
    "BAL": "p2",  # Orioles (Away team) maps to p2
    "50-50": "p3",  # Tie or undetermined maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Sensitive data patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"SPORTS_DATA_IO_MLB_API_KEY\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"api_key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"Authorization\s*:\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    # Add more patterns as needed
]

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        original_msg = record.getMessage()
        masked_msg = original_msg
        for pattern in SENSITIVE_PATTERNS:
            masked_msg = pattern.sub("******", masked_msg)
        record.msg = masked_msg
        return True

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

console_handler.addFilter(SensitiveDataFilter())

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
        # Build mapping from full team name to API abbreviation
        return {f"{team['City']} {team['Name']}": team['Key'] for team in teams}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch team abbreviations: {e}")
        return {}

def fetch_game_data(date, team1_name, team2_name, team_abbreviation_map=None):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_name: First team name (full name or abbreviation)
        team2_name: Second team name (full name or abbreviation)
        team_abbreviation_map: Optional mapping of team names to abbreviations

    Returns:
        Game data dictionary or None if not found
    """
    logger.info(f"Fetching game data for game between {team1_name} and {team2_name} on {date}")
    
    # If we don't have a team abbreviation map, try to get one
    if team_abbreviation_map is None:
        team_abbreviation_map = get_team_abbreviation_map()
    
    # Convert team names to abbreviations if needed
    team1_api = team_abbreviation_map.get(team1_name, team1_name)
    team2_api = team_abbreviation_map.get(team2_name, team2_name)
    
    logger.info(f"Using team abbreviations: {team1_api} and {team2_api}")

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/mlb/stats/json/BoxScoresFinal/{date}?key={API_KEY}"
    
    # Mask API key in logs
    masked_url = url.replace(API_KEY, "******")
    logger.debug(f"Using API endpoint: {masked_url}")

    try:
        logger.debug("Sending API request")
        response = requests.get(url)

        if response.status_code == 404:
            logger.warning(
                f"No data found for {date}. Please check the date and ensure data is available."
            )
            return None

        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            game_info = game_data.get("Game", {})
            home_team = game_info.get("HomeTeam")
            away_team = game_info.get("AwayTeam")
            
            logger.debug(f"Checking game: {away_team} vs {home_team}")
            
            # Check if either team matches our search
            if (home_team == team1_api and away_team == team2_api) or (home_team == team2_api and away_team == team1_api):
                logger.info(f"Found matching game: {away_team} @ {home_team}")
                
                # Store the team IDs for later use
                game_data["team1"] = team1_api
                game_data["team2"] = team2_api
                return game_data

        logger.warning(
            f"No matching game found between {team1_api} and {team2_api} on {date}."
        )
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse API response: {e}")
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
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    # Extract game info from the nested structure
    game_info = game.get("Game", {})

    status = game_info.get("Status")
    home_score = game_info.get("HomeTeamRuns")
    away_score = game_info.get("AwayTeamRuns")
    home_team = game_info.get("HomeTeam")
    away_team = game_info.get("AwayTeam")
    
    team1 = game.get("team1")
    team2 = game.get("team2")

    logger.info(
        f"Game status: {status}, Score: {away_team} {away_score} - {home_team} {home_score}"
    )

    if status in ["Scheduled", "Delayed", "InProgress", "Suspended"]:
        logger.info(f"Game is {status}, too early to resolve")
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Postponed", "Canceled"]:
        logger.info(f"Game was {status}, resolving as 50-50")
        return RESOLUTION_MAP["50-50"]
    elif status == "Final":
        if home_score is not None and away_score is not None:
            if home_score == away_score:
                logger.info("Game ended in a tie, resolving as 50-50")
                return RESOLUTION_MAP["50-50"]
            elif home_score > away_score:
                # Determine which team ID corresponds to the winner (home team)
                if home_team == team1:
                    winner_team = team1
                else:
                    winner_team = team2
                    
                logger.info(f"Home team ({home_team}) won")
                # Return the appropriate outcome based on the winning team
                if winner_team in RESOLUTION_MAP:
                    return RESOLUTION_MAP[winner_team]
                else:
                    logger.warning(f"Missing resolution mapping for team {winner_team}")
                    return RESOLUTION_MAP["50-50"]
            else:
                # Determine which team ID corresponds to the winner (away team)
                if away_team == team1:
                    winner_team = team1
                else:
                    winner_team = team2
                    
                logger.info(f"Away team ({away_team}) won")
                # Return the appropriate outcome based on the winning team
                if winner_team in RESOLUTION_MAP:
                    return RESOLUTION_MAP[winner_team]
                else:
                    logger.warning(f"Missing resolution mapping for team {winner_team}")
                    return RESOLUTION_MAP["50-50"]

    logger.warning(
        f"Unexpected game state: {status}, defaulting to 'Too early to resolve'"
    )
    return RESOLUTION_MAP["Too early to resolve"]


def main():
    """
    Main function to query MLB game data and determine the resolution.
    This sample uses hardcoded values but could be modified to extract
    information directly from a query.
    """
    # Sample date and teams - in a real implementation, these would be
    # extracted from the user query
    date = "2025-03-30"
    team1_name = "Toronto Blue Jays"
    team2_name = "Baltimore Orioles"
    
    # Get the team abbreviation map
    team_abbreviation_map = get_team_abbreviation_map()
    if not team_abbreviation_map:
        logger.error("Failed to retrieve team abbreviations")
        print(f"recommendation: {RESOLUTION_MAP['Too early to resolve']}")
        return
    
    # Fetch game data
    game = fetch_game_data(date, team1_name, team2_name, team_abbreviation_map)
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(f"recommendation: {resolution}")


if __name__ == "__main__":
    main()
