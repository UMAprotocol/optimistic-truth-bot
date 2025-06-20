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

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Leon Draisaitl scores more than 0.5 goals
    "No": "p1",   # Leon Draisaitl scores 0.5 goals or less
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

# Function to check if Leon Draisaitl scored in the game
def check_draisaitl_score(game_id):
    url = f"{PRIMARY_ENDPOINT}/scores/json/BoxScore/{game_id}"
    data = make_request(url, HEADERS)
    if data:
        for player in data['PlayerGames']:
            if player['Name'] == "Leon Draisaitl" and player['Goals'] > 0.5:
                return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-12"
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > "2025-12-31":
        return RESOLUTION_MAP["50-50"]

    # Find the game ID for the specific match
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] == "EDM" and game['AwayTeam'] == "FLA":
                result = check_draisaitl_score(game['GameID'])
                return RESOLUTION_MAP[result]

    return RESOLUTION_MAP["50-50"]

# Run the main function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")