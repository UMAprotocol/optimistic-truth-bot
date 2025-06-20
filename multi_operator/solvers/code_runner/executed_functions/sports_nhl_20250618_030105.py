import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to fetch data from API with fallback to proxy
def fetch_data(url, params=None):
    try:
        response = requests.get(f"{PRIMARY_ENDPOINT}{url}", headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to proxy endpoint if primary fails
            response = requests.get(f"{PROXY_ENDPOINT}{url}", headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

# Function to check if Evan Bouchard scored a goal
def check_goals(game_id):
    game_stats = fetch_data(f"/scores/json/PlayerGameStatsByGame/{game_id}")
    if game_stats:
        for player_stat in game_stats:
            if player_stat['Name'] == "Evan Bouchard" and player_stat['Goals'] > 0:
                return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Date and teams for the game
    game_date = "2025-06-17"
    teams = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

    # Fetch games on the specified date
    games = fetch_data(f"/scores/json/GamesByDate/{game_date}")
    if games:
        for game in games:
            if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
                # Check if Evan Bouchard scored a goal
                result = check_goals(game['GameID'])
                recommendation = RESOLUTION_MAP[result]
                return f"recommendation: {recommendation}"

    # If no games found or not completed by the specified future date
    return "recommendation: p3"

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())