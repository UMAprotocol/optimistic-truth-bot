import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError("SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. Please add it to your .env file.")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Khachanov": "p2",  # Khachanov wins
    "Rune": "p1",       # Rune wins
    "50-50": "p3",      # Tie or undetermined
    "Too early to resolve": "p4"  # Incomplete data
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_match_result():
    """
    Fetches the match result from the Sports Data IO API.
    """
    url = f"https://api.sportsdata.io/v3/tennis/scores/json/PlayerMatchStatsByDate/2025-04-19?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        matches = response.json()
        for match in matches:
            if match['Tournament']['Name'] == "Barcelona Open" and match['Round'] == "Semi-Finals":
                player1 = match['Player1']['LastName']
                player2 = match['Player2']['LastName']
                if player1 == "Khachanov" and player2 == "Rune":
                    if match['Winner'] == "Player1":
                        return "Khachanov"
                    elif match['Winner'] == "Player2":
                        return "Rune"
        return "50-50"  # No clear winner or match not found
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch match result: {e}")
        return "Too early to resolve"

def main():
    """
    Main function to determine the resolution of the tennis match.
    """
    result = fetch_match_result()
    resolution = RESOLUTION_MAP.get(result, "p4")
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()