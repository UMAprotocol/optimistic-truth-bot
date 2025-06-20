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
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
MATCH_DATE = "2025-06-17"
PLAYER1 = "Jordan Thompson"
PLAYER2 = "Jaume Munar"

# Function to fetch match data
def fetch_match_data():
    try:
        response = requests.get(HSBC_CHAMPIONSHIPS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine match outcome
def determine_outcome(match_data):
    if not match_data:
        return "p3"  # Assume 50-50 if no data could be fetched

    for match in match_data:
        if (match['date'] == MATCH_DATE and
            PLAYER1 in match['players'] and
            PLAYER2 in match['players']):
            if match['status'] == "completed":
                winner = match['winner']
                if winner == PLAYER1:
                    return "p2"  # Thompson wins
                elif winner == PLAYER2:
                    return "p1"  # Munar wins
            elif match['status'] in ["canceled", "postponed"]:
                return "p3"  # 50-50 for canceled or postponed
    return "p3"  # Default to 50-50 if no specific match info found

# Main execution
if __name__ == "__main__":
    match_data = fetch_match_data()
    outcome = determine_outcome(match_data)
    print(f"recommendation: {outcome}")