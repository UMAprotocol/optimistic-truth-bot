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

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "AC Milan": "p2",  # AC Milan advances
    "Inter Milan": "p1",  # Inter Milan advances
    "50-50": "p3",  # Match canceled or postponed
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

def fetch_match_data():
    """
    Fetches match data for the Coppa Italia Semifinal between AC Milan and Inter Milan.

    Returns:
        Match data dictionary or None if not found
    """
    logger.info("Fetching match data for Coppa Italia Semifinal between AC Milan and Inter Milan")
    
    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/soccer/scores/json/GamesByDate/{datetime.now().strftime('%Y-%m-%d')}?key={API_KEY}"
    
    try:
        logger.debug("Sending API request")
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        logger.info(f"Retrieved {len(matches)} matches for today")

        # Find the specific match - the API returns an array of match objects
        for match_data in matches:
            if "AC Milan" in match_data['HomeTeamName'] and "Inter Milan" in match_data['AwayTeamName']:
                logger.info("Found matching match: AC Milan vs Inter Milan")
                return match_data

        logger.warning("No matching match found for AC Milan vs Inter Milan today.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(match):
    """
    Determines the resolution based on the match's status and outcome.

    Args:
        match: Match data dictionary from the API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not match:
        logger.info("No match data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    status = match.get("Status")
    home_score = match.get("HomeTeamScore")
    away_score = match.get("AwayTeamScore")
    
    logger.info(f"Match status: {status}, Score: AC Milan {home_score} - Inter Milan {away_score}")

    if status in ["Scheduled", "InProgress"]:
        logger.info(f"Match is {status}, too early to resolve")
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Final"]:
        if home_score > away_score:
            logger.info("AC Milan advances")
            return RESOLUTION_MAP["AC Milan"]
        elif away_score > home_score:
            logger.info("Inter Milan advances")
            return RESOLUTION_MAP["Inter Milan"]
        else:
            logger.info("Match ended in a draw, resolving as 50-50")
            return RESOLUTION_MAP["50-50"]
    elif status in ["Canceled", "Postponed"]:
        logger.info(f"Match was {status}, resolving as 50-50")
        return RESOLUTION_MAP["50-50"]

    logger.warning(f"Unexpected match state: {status}, defaulting to 'Too early to resolve'")
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query match data and determine the resolution.
    """
    # Fetch match data
    match = fetch_match_data()
    
    # Determine resolution
    resolution = determine_resolution(match)
    
    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()