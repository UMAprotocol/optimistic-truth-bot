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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
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
    except requests.RequestException:
        return None

# Function to check if Brad Marchand scored a goal
def check_goals(game_data):
    for player in game_data.get('PlayerStats', []):
        if player.get('Name') == "Brad Marchand":
            goals = player.get('Goals', 0)
            return "Yes" if goals > 0.5 else "No"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Date and teams based on the user prompt
    game_date = "2025-06-12"
    teams = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

    # Try proxy endpoint first
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{game_date}")
    if not games_today:
        # Fallback to primary endpoint if proxy fails
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{game_date}")

    if not games_today:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    # Find the specific game
    for game in games_today:
        if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
            if game['Status'] == "Final":
                result = check_goals(game)
                return "recommendation: " + RESOLUTION_MAP[result]
            else:
                return "recommendation: " + RESOLUTION_MAP["50-50"]

    return "recommendation: " + RESOLUTION_MAP["50-50"]

# Execute the function and print the result
if __name__ == "__main__":
    print(resolve_market())