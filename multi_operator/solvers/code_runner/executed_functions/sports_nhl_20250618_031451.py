import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Yes": "p2",  # Brad Marchand scores more than 0.5 goals
    "No": "p1",   # Brad Marchand scores 0.5 goals or less
    "50-50": "p3" # Game not completed by the specified date
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Brad Marchand scored in the game
def check_marchand_score(game_id):
    url = f"{PRIMARY_ENDPOINT}/scores/json/BoxScore/{game_id}"
    data = make_request(url, HEADERS)
    if data:
        for player in data['PlayerGames']:
            if player['Name'] == "Brad Marchand":
                goals = player['Goals']
                return "Yes" if goals > 0.5 else "No"
    return "No"

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-17"
    teams = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
                if datetime.now() > datetime(2025, 12, 31, 23, 59):
                    return RESOLUTION_MAP["50-50"]
                return RESOLUTION_MAP[check_marchand_score(game['GameID'])]
    return RESOLUTION_MAP["50-50"]

# Execute the main function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")