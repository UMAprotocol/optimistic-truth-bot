import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HSBC_CHAMPIONSHIPS_URL = "https://www.lta.org.uk/fan-zone/international/hsbc-championships/"
MATCH_DATE = "2025-06-17"
PLAYER1 = "Carlos Alcaraz"
PLAYER2 = "Alejandro Davidovich Fokina"
TIMEOUT = 10

# Headers for requests
HEADERS = {
    "Ocp-Apim-Subscription-Key": API_KEY
}

def get_match_result():
    try:
        response = requests.get(HSBC_CHAMPIONSHIPS_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        # Assuming the website provides JSON data with match results
        data = response.json()
        for match in data.get('matches', []):
            if (match['date'] == MATCH_DATE and
                PLAYER1 in match['players'] and
                PLAYER2 in match['players']):
                if match['winner'] == PLAYER1:
                    return "p2"  # Alcaraz wins
                elif match['winner'] == PLAYER2:
                    return "p1"  # Fokina wins
                else:
                    return "p3"  # Match tie or no clear winner
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Resolve to 50-50 in case of data fetch failure or error

    # If no data matched or in case of other issues, default to unknown
    return "p3"

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")