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
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_match_result():
    """
    Fetches the result of the UEFA Europa League match between Athletic Club and Rangers.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-17?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        matches = response.json()
        
        for match in matches:
            if match['HomeTeam'] == 'ATH' and match['AwayTeam'] == 'RAN':
                if match['Status'] == 'Final':
                    home_score = match['HomeTeamScore']
                    away_score = match['AwayTeamScore']
                    if home_score > away_score:
                        return "p2"  # Athletic Club advances
                    elif away_score > home_score:
                        return "p1"  # Rangers advances
                elif match['Status'] in ['Canceled', 'Postponed']:
                    return "p3"  # Match canceled or postponed
        return "p3"  # No match found or no clear result, resolve 50-50
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return "p3"  # Resolve 50-50 in case of API failure

def main():
    """
    Main function to determine the outcome of the UEFA Europa League match.
    """
    result = fetch_match_result()
    print(f"recommendation: {RESOLUTION_MAP.get(result, 'p3')}")

if __name__ == "__main__":
    main()