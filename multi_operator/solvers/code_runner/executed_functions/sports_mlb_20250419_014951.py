import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_miami_heat_playoff_status():
    """
    Checks if Miami Heat has made the NBA Playoffs for the 2024-25 season.
    """
    if not API_KEY:
        logging.error("API key for Sports Data IO NBA is not set.")
        return "p3"  # Unknown due to configuration error

    url = "https://api.sportsdata.io/v3/nba/scores/json/Standings/2025"
    headers = {
        "Ocp-Apim-Subscription-Key": API_KEY
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        standings = response.json()

        # Check if Miami Heat is in the top 8 of their conference
        for team in standings:
            if team["Team"] == "MIA" and team["ConferenceRank"] <= 8:
                logging.info("Miami Heat has made the playoffs.")
                return RESOLUTION_MAP["Yes"]
        
        logging.info("Miami Heat has not made the playoffs.")
        return RESOLUTION_MAP["No"]

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch or process data: {e}")
        return RESOLUTION_MAP["Unknown"]

def main():
    """
    Main function to determine if Miami Heat made the NBA Playoffs.
    """
    result = check_miami_heat_playoff_status()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()