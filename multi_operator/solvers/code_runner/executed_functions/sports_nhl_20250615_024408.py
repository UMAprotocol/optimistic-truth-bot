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
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data from API: {e}")
            return None

# Function to check if Corey Perry scored in the game
def check_corey_perry_score(game_id):
    game_stats = make_request(f"/scores/json/PlayerGameStatsByGame/{game_id}")
    if game_stats:
        for player_stat in game_stats:
            if player_stat["Name"] == "Corey Perry" and player_stat["Goals"] > 0:
                return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Date and teams from the ancillary data
    game_date = "2025-06-14"
    teams = ["Edmonton Oilers", "Florida Panthers"]

    # Find the game ID
    games_on_date = make_request(f"/scores/json/GamesByDate/{game_date}")
    if games_on_date:
        for game in games_on_date:
            if game["HomeTeam"] in teams and game["AwayTeam"] in teams:
                result = check_corey_perry_score(game["GameID"])
                return f"recommendation: {RESOLUTION_MAP[result]}"

    # If no game is found or no data available, assume 50-50 if past the deadline
    current_date = datetime.now()
    deadline_date = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    if current_date > deadline_date:
        return "recommendation: p3"
    else:
        return "recommendation: p4"

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())