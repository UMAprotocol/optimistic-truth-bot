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

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Function to check if Evan Bouchard scored a goal
def check_goals(game_data):
    for player in game_data.get('PlayerStats', []):
        if player.get('Name') == "Evan Bouchard" and player.get('Goals', 0) > 0.5:
            return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Date of the game
    game_date = "2025-06-12"
    # Try proxy endpoint first
    game_data = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{game_date}")
    if not game_data:
        # Fallback to primary endpoint if proxy fails
        game_data = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{game_date}")
    
    if not game_data:
        return "recommendation: p4"  # Unable to retrieve data

    # Check if the game was completed
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    if current_date <= game_date:
        return "recommendation: p4"  # Game has not occurred yet

    # Check if Evan Bouchard scored a goal
    result = check_goals(game_data)
    return f"recommendation: {RESOLUTION_MAP[result]}"

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())