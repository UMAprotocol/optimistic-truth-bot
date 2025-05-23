import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "ATH": "p2",  # Athletic Club
    "RAN": "p1",  # Rangers
    "50-50": "p3",
    "Too early to resolve": "p4",
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
    Fetches the result of the UEFA Europa League match between Athletic Club and Rangers.
    """
    url = f"https://api.sportsdata.io/v3/soccer/scores/json/GamesByDate/2025-04-17?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        matches = response.json()
        
        for match in matches:
            if match['HomeTeamName'] == "Athletic Club" and match['AwayTeamName'] == "Rangers":
                if match['Status'] == "Final":
                    home_score = match['HomeTeamScore']
                    away_score = match['AwayTeamScore']
                    if home_score > away_score:
                        return "p2"  # Athletic Club advances
                    elif away_score > home_score:
                        return "p1"  # Rangers advances
                    else:
                        return "p3"  # Draw or unresolved, treat as 50-50
                elif match['Status'] in ["Canceled", "Postponed"]:
                    return "p3"  # Match canceled or postponed, resolve as 50-50
        return "p4"  # No match found or not yet played
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch match result: {e}")
        return "p4"  # Default to unresolved if there's an error

def main():
    """
    Main function to determine the outcome of the UEFA Europa League match.
    """
    result = fetch_match_result()
    print(f"recommendation: {RESOLUTION_MAP.get(result, 'p4')}")

if __name__ == "__main__":
    main()