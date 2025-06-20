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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution conditions
RESOLUTION_MAP = {
    "YES": "p2",  # Player scored more than 0.5 goals
    "NO": "p1",   # Player did not score more than 0.5 goals
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
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check if Carter Verhaeghe scored in the specified game
def check_player_score(game_id, player_name="Carter Verhaeghe"):
    game_stats = make_request(f"/scores/json/PlayerGameStatsByGame/{game_id}")
    if game_stats:
        for player_stat in game_stats:
            if player_stat.get("Name") == player_name:
                goals = player_stat.get("Goals", 0)
                return "YES" if goals > 0.5 else "NO"
    return "50-50"

# Main function to resolve the market
def resolve_market():
    # Date and teams for the game
    game_date = "2025-06-12"
    teams = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

    # Find the game by date and teams
    games_on_date = make_request(f"/scores/json/GamesByDate/{game_date}")
    if games_on_date:
        for game in games_on_date:
            if game["HomeTeam"] in teams and game["AwayTeam"] in teams:
                game_id = game["GameID"]
                result = check_player_score(game_id)
                return f"recommendation: {RESOLUTION_MAP[result]}"

    # If no game found or no result, assume 50-50 if past the deadline
    current_date = datetime.now()
    deadline = datetime(2025, 12, 31, 23, 59)
    if current_date > deadline:
        return f"recommendation: {RESOLUTION_MAP['50-50']}"
    else:
        return "recommendation: p4"  # Game not yet played or data not available

# Run the resolver
if __name__ == "__main__":
    print(resolve_market())