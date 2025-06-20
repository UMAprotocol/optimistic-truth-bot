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
DATE = "2025-06-19"
PLAYER1 = "Shapovalov"
PLAYER2 = "Cobolli"
TOURNAMENT = "Terra Wortmann Open"
MATCH_URL = "https://www.terrawortmann-open.de/en/"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_match_result():
    try:
        # Simulating an API call to get match results
        # This is a placeholder for the actual API call which should be implemented according to the API's documentation
        response = requests.get(MATCH_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Process the response to determine the match outcome
            # This is a simplified example assuming the response contains the match winner directly
            match_data = response.json()
            if PLAYER1 in match_data['winner']:
                return "p2"  # Shapovalov wins
            elif PLAYER2 in match_data['winner']:
                return "p1"  # Cobolli wins
            else:
                return "p3"  # Match tie, canceled, or delayed
        else:
            return "p3"  # Assuming match tie, canceled, or delayed if API call fails
    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return "p3"  # Safe fallback in case of request failure

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")