import os
import requests
from dotenv import load_dotenv
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NHL_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using team abbreviations
RESOLUTION_MAP = {
    "VGK": "p2",  # Vegas Golden Knights maps to p2
    "CGY": "p1",  # Calgary Flames maps to p1
    "50-50": "p3",  # Canceled or unresolved maps to p3
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

def fetch_game_data(date):
    """
    Fetches game data for the specified date.

    Args:
        date: Game date in YYYY-MM-DD format

    Returns:
        Game data dictionary or None if not found
    """
    logger.info(f"Fetching game data for NHL on {date}")
    
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")
        return games
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(games):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        games: List of game data dictionaries from the API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    for game in games:
        if game['HomeTeam'] == "VGK" or game['AwayTeam'] == "VGK":
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score and game['HomeTeam'] == "VGK":
                    return "recommendation: " + RESOLUTION_MAP["VGK"]
                elif away_score > home_score and game['AwayTeam'] == "VGK":
                    return "recommendation: " + RESOLUTION_MAP["VGK"]
                elif home_score > away_score and game['HomeTeam'] == "CGY":
                    return "recommendation: " + RESOLUTION_MAP["CGY"]
                elif away_score > home_score and game['AwayTeam'] == "CGY":
                    return "recommendation: " + RESOLUTION_MAP["CGY"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query NHL game data and determine the resolution.
    """
    date = "2025-04-15"
    
    # Fetch game data
    games = fetch_game_data(date)
    
    if games is None:
        print("recommendation: " + RESOLUTION_MAP["Too early to resolve"])
        return
    
    # Determine resolution
    resolution = determine_resolution(games)
    
    # Output the recommendation
    print(resolution)

if __name__ == "__main__":
    main()