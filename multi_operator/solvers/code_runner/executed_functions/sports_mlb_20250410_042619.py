import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "No": "p1",  # Team did not make the playoffs
    "Yes": "p2",  # Team made the playoffs
    "Unknown": "p3",  # Outcome is unknown or 50-50
    "Too early to resolve": "p4",  # Not enough data
}

logger = logging.getLogger(__name__)

def fetch_nba_playoff_status(team_name):
    """
    Fetches NBA playoff status for the specified team.

    Args:
        team_name: Name of the NBA team

    Returns:
        Playoff status as a string ("Yes", "No", "Unknown", or "Too early to resolve")
    """
    logger.info(f"Fetching NBA playoff status for {team_name}")

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key={API_KEY}"

    logger.debug(f"Using API endpoint: {url}")

    try:
        logger.debug("Sending API request")
        response = requests.get(url)
        response.raise_for_status()
        standings = response.json()
        logger.info("Retrieved NBA standings data")

        # Check if the team is in the top 16 of either conference
        for entry in standings:
            if entry["Team"] == team_name and entry["PlayoffRank"] <= 16:
                logger.info(f"{team_name} is in the playoffs")
                return "Yes"
        logger.info(f"{team_name} did not make the playoffs")
        return "No"

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return "Too early to resolve"
    except ValueError as e:
        logger.error(f"Failed to parse API response: {e}")
        return "Unknown"

def main():
    team_name = "Phoenix Suns"
    playoff_status = fetch_nba_playoff_status(team_name)
    resolution = RESOLUTION_MAP.get(playoff_status, "Too early to resolve")
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()