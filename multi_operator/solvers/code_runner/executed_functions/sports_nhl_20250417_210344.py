import os
import requests
from dotenv import load_dotenv
from datetime import datetime
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

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "ATH": "p2",  # Athletic Club maps to p2
    "RAN": "p1",  # Rangers maps to p1
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
    Fetches match data for the UEFA Europa League Quarterfinal match between Athletic Club and Rangers.

    Returns:
        Match data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{datetime.now().strftime('%Y-%m-%d')}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        for match in matches:
            if match['HomeTeam'] == 'ATH' and match['AwayTeam'] == 'RAN':
                return match
            elif match['HomeTeam'] == 'RAN' and match['AwayTeam'] == 'ATH':
                return match
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch match data: {e}")
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

    if match['Status'] == 'Final':
        if match['HomeTeamRuns'] > match['AwayTeamRuns']:
            winner = match['HomeTeam']
        else:
            winner = match['AwayTeam']

        if winner == 'ATH':
            return RESOLUTION_MAP['ATH']
        elif winner == 'RAN':
            return RESOLUTION_MAP['RAN']
    elif match['Status'] in ['Canceled', 'Postponed']:
        return RESOLUTION_MAP['50-50']
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query UEFA Europa League match data and determine the resolution.
    """
    match = fetch_match_data()
    resolution = determine_resolution(match)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()