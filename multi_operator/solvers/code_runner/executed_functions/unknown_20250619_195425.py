import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to perform GET requests with error handling and fallback mechanism
def get_request(url, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the match
def determine_outcome(data, player1, player2):
    if not data:
        return "p3"  # Unknown or 50-50 if no data available
    for match in data:
        if match['player1'] == player1 and match['player2'] == player2:
            if match['winner'] == player1:
                return "p1"
            elif match['winner'] == player2:
                return "p2"
    return "p3"  # Default to 50-50 if no exact match found

# Main function to execute the logic
def main():
    # Match details
    date_of_match = "2025-06-19"
    player1 = "Jannik Sinner"
    player2 = "Alexander Bublik"
    tournament_url = "https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate/2025-06-19"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

    # Fetch data
    match_data = get_request(tournament_url, proxy_url)

    # Determine the outcome
    result = determine_outcome(match_data, player1, player2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()