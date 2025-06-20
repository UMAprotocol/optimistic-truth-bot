import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Brad Marchand"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to check if Brad Marchand scored a goal
def check_goals(game_data):
    for player in game_data.get('PlayerStats', []):
        if player.get('Name') == PLAYER_NAME and player.get('Goals', 0) > 0.5:
            return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    if current_date > "2025-12-31":
        return RESOLUTION_MAP["50-50"]

    # Construct URL for game data
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"

    # Try proxy first
    game_data = make_request(PROXY_ENDPOINT, HEADERS)
    if not game_data:
        # Fallback to primary endpoint if proxy fails
        game_data = make_request(url, HEADERS)

    if not game_data:
        return RESOLUTION_MAP["50-50"]

    # Check each game for the specific teams and date
    for game in game_data:
        if game['HomeTeam'] in TEAM_ABBREVIATIONS.values() and game['AwayTeam'] in TEAM_ABBREVIATIONS.values():
            if game['Status'] == "Final":
                result = check_goals(game)
                return RESOLUTION_MAP[result]
            elif game['Status'] in ["Scheduled", "InProgress"]:
                return RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["50-50"]

# Run the resolver function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")