import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NBA_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Inter Milan": "p1",  # Inter Milan maps to p1
    "AC Milan": "p2",  # AC Milan maps to p2
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

def fetch_match_data():
    """
    Fetches match data for the Coppa Italia Semifinal between AC Milan and Inter Milan.

    Returns:
        Match outcome or None if not found
    """
    logger.info("Fetching match data for Coppa Italia Semifinal between AC Milan and Inter Milan")
    
    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/soccer/scores/json/GamesByDate/{datetime.now().strftime('%Y-%m-%d')}?key={API_KEY}"
    
    try:
        logger.debug("Sending API request")
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            logger.warning(
                "No data found for today. Please check the date and ensure data is available."
            )
            return None

        response.raise_for_status()
        matches = response.json()
        logger.info(f"Retrieved {len(matches)} matches for today")

        # Find the specific match - the API returns an array of match objects
        for match_data in matches:
            if "AC Milan" in match_data['HomeTeamName'] and "Inter Milan" in match_data['AwayTeamName']:
                logger.info("Found matching match: AC Milan vs Inter Milan")
                return match_data

        logger.warning("No matching match found between AC Milan and Inter Milan.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(match):
    """
    Determines the resolution based on the match's outcome.

    Args:
        match: Match data dictionary from the API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not match:
        logger.info("No match data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    status = match.get("Status")
    logger.info(f"Match status: {status}")

    if status == "Final":
        home_score = match.get("HomeTeamScore")
        away_score = match.get("AwayTeamScore")
        
        if home_score > away_score:
            logger.info("AC Milan advances to the next round")
            return RESOLUTION_MAP["AC Milan"]
        elif away_score > home_score:
            logger.info("Inter Milan advances to the next round")
            return RESOLUTION_MAP["Inter Milan"]
        else:
            logger.info("Match ended in a draw, resolving as 50-50")
            return RESOLUTION_MAP["50-50"]
    else:
        logger.info("Match is not yet final, resolving as 'Too early to resolve'")
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