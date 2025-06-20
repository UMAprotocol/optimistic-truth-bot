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
DATE = "2025-06-17"
PLAYER1 = "Joao Fonseca"
PLAYER2 = "Flavio Cobolli"
TOURNAMENT = "Terra Wortmann Open"
MATCH_URL = "https://www.terrawortmann-open.de/en/"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_match_result():
    try:
        # Simulating API call to get match results
        # This is a placeholder for the actual API call which should be implemented according to the API's documentation
        response = requests.get(MATCH_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Process the response to find the match result
            # This is a simplified example of how you might parse the response
            if PLAYER1 in response.text and "advances" in response.text:
                return "p2"  # Fonseca wins
            elif PLAYER2 in response.text and "advances" in response.text:
                return "p1"  # Cobolli wins
            else:
                return "p3"  # Match tie, canceled, or delayed
        else:
            return "p3"  # Unable to determine, default to 50-50
    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return "p3"  # Default to 50-50 in case of error

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")