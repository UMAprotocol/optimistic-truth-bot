import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Khachanov": "p2",  # Khachanov advances
    "Rune": "p1",       # Rune advances
    "50-50": "p3",      # Tie, canceled, or delayed
    "Too early to resolve": "p4",  # Incomplete data
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_match_result():
    """
    Fetches the result of the tennis match from the Sports Data IO API.
    """
    url = f"https://api.sportsdata.io/v3/tennis/scores/json/PlayerSeasonStats/2025?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Example of processing data to find match result
        for match in data:
            if match['Tournament'] == 'Barcelona Open' and match['Round'] == 'Semi-finals':
                player1 = match['Player1']
                player2 = match['Player2']
                if player1 == 'Karen Khachanov' and player2 == 'Holger Rune':
                    if match['Winner'] == 'Karen Khachanov':
                        return "p2"
                    elif match['Winner'] == 'Holger Rune':
                        return "p1"
        return "p3"  # Assume 50-50 if no specific winner is found or match data is missing
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch match result: {e}")
        return "p4"  # Return "Too early to resolve" if there is an error in fetching data

def main():
    """
    Main function to determine the outcome of the tennis match.
    """
    result_code = fetch_match_result()
    recommendation = RESOLUTION_MAP.get(result_code, "p4")
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()