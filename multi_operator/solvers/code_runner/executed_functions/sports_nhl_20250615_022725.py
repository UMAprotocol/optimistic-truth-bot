import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# NHL Game and Player Information
GAME_DATE = "2025-06-14"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
PLAYER_NAME = "Connor McDavid"

# Resolution conditions mapping
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_api_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to check if the player scored in the game
def check_player_score(game_id, player_name):
    url = f"{PROXY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_api_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0.5:
                return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    current_date = datetime.now()
    deadline_date = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    if current_date > deadline_date:
        return RESOLUTION_MAP["50-50"]

    # Construct the URL to fetch game data
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    games = make_api_request(url, HEADERS)
    if games:
        for game in games:
            if {game['HomeTeam'], game['AwayTeam']} == set(TEAM_ABBREVIATIONS.values()):
                if game['Status'] != "Final":
                    return RESOLUTION_MAP["50-50"]
                result = check_player_score(game['GameID'], PLAYER_NAME)
                return RESOLUTION_MAP[result]
    return RESOLUTION_MAP["50-50"]

# Run the main function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")