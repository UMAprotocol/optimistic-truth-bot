import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Royal Challengers Bangalore": "p2",  # Royal Challengers Bangalore win maps to p2
    "Rajasthan Royals": "p1",  # Rajasthan Royals win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
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
    date = "2025-04-24"
    team1_name = "Royal Challengers Bangalore"
    team2_name = "Rajasthan Royals"
    
    logger.info(f"Fetching game data for game between {team1_name} and {team2_name} on {date}")

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/mlb/stats/json/BoxScoresFinal/{date}?key={API_KEY}"
    
    try:
        logger.debug("Sending API request")
        response = requests.get(url, timeout=10)

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
            if (home_team == team1_name and away_team == team2_name) or (home_team == team2_name and away_team == team1_name):
                logger.info(f"Found matching game: {away_team} @ {home_team}")
                return game_data

        logger.warning(
            f"No matching game found between {team1_name} and {team2_name} on {date}."
        )
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
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    # Extract game info from the nested structure
    game_info = game.get("Game", {})

    status = game_info.get("Status")
    home_score = game_info.get("HomeTeamRuns")
    away_score = game_info.get("AwayTeamRuns")
    home_team = game_info.get("HomeTeam")
    away_team = game_info.get("AwayTeam")

    logger.info(
        f"Game status: {status}, Score: {away_team} {away_score} - {home_team} {home_score}"
    )

    if status in ["Scheduled", "Delayed", "InProgress", "Suspended"]:
        logger.info(f"Game is {status}, too early to resolve")
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Postponed"]:
        logger.info(f"Game was {status}, market remains open")
        return RESOLUTION_MAP["Too early to resolve"]
    elif status == "Canceled":
        logger.info(f"Game was {status}, resolving as 50-50")
        return RESOLUTION_MAP["50-50"]
    elif status == "Final":
        if home_score > away_score:
            winner_team = home_team
        else:
            winner_team = away_team

        logger.info(f"Winner: {winner_team}")
        return RESOLUTION_MAP.get(winner_team, RESOLUTION_MAP["50-50"])

    logger.warning(
        f"Unexpected game state: {status}, defaulting to 'Too early to resolve'"
    )
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query IPL game data and determine the resolution.
    """
    # Fetch game data
    game = fetch_game_data()
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()