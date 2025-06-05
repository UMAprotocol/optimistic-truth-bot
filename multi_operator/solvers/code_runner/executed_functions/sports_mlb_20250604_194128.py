import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map for outcomes
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error with primary endpoint, trying proxy: {e}")
        response = requests.get(f"{PROXY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

# Function to check if Hakimi Achraf scored in the final
def check_hakimi_score():
    date_of_final = "2025-05-31"
    try:
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_of_final}")
        for game in games:
            if game['Status'] == 'Final' and {'Paris Saint-Germain', 'Inter Milan'} == {game['HomeTeam'], game['AwayTeam']}:
                player_stats = make_request(PRIMARY_ENDPOINT, f"PlayerGameStatsByGame/{game['GameID']}")
                for player in player_stats:
                    if player['Name'] == 'Hakimi Achraf' and player['Scoring']['Goals'] > 0.5:
                        return RESOLUTION_MAP["Yes"]
        return RESOLUTION_MAP["No"]
    except Exception as e:
        print(f"An error occurred: {e}")
        return RESOLUTION_MAP["50-50"]

# Main execution
if __name__ == "__main__":
    result = check_hakimi_score()
    print(f"recommendation: {result}")