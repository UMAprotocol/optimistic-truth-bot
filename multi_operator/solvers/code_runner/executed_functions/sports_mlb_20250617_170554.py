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
RESOLUTION_MAP = {
    "Thompson": "p2",
    "Munar": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to fetch match data
def fetch_match_data():
    try:
        response = requests.get(HSBC_CHAMPIONSHIPS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome
def determine_outcome(data):
    if not data:
        return RESOLUTION_MAP["Too early to resolve"]
    
    for match in data.get('matches', []):
        if match['date'] == MATCH_DATE and PLAYER1 in match['players'] and PLAYER2 in match['players']:
            if match['status'] == 'completed':
                winner = match['winner']
                if winner == PLAYER1:
                    return RESOLUTION_MAP["Thompson"]
                elif winner == PLAYER2:
                    return RESOLUTION_MAP["Munar"]
            elif match['status'] in ['canceled', 'postponed']:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    match_data = fetch_match_data()
    recommendation = determine_outcome(match_data)
    print(f"recommendation: {recommendation}")