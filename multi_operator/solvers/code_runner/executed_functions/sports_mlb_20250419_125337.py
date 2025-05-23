import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Khachanov": "p2",
    "Rune": "p1",
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
    Fetches the result of the tennis match from the specified API endpoint.
    """
    url = "https://api.sportsdata.io/v3/tennis/scores/json/PlayerTournamentStatsByPlayer/2025"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        matches = response.json()

        for match in matches:
            if match['Tournament']['Name'] == "Barcelona Open" and match['Round'] == "Semi-Finals":
                player1 = match['Player1']['FullName']
                player2 = match['Player2']['FullName']
                if "Karen Khachanov" in player1 or "Karen Khachanov" in player2:
                    if "Holger Rune" in player1 or "Holger Rune" in player2:
                        winner = match['Winner']['FullName']
                        if winner == "Karen Khachanov":
                            return "p2"
                        elif winner == "Holger Rune":
                            return "p1"
        return "p3"  # If no specific winner is found, resolve as 50-50
    except requests.RequestException as e:
        logger.error(f"Failed to fetch match result: {e}")
        return "p4"  # Return "Too early to resolve" in case of any error

def main():
    """
    Main function to determine the outcome of the tennis match.
    """
    result = fetch_match_result()
    print(f"recommendation: {RESOLUTION_MAP.get(result, 'p4')}")

if __name__ == "__main__":
    main()