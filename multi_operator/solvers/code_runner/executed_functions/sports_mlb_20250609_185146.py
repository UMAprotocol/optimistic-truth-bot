import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check player's score
def check_player_score(game_date, player_name):
    # Format date for API endpoint
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if not games:
        # Fallback to proxy if primary fails
        games = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")
        if not games:
            return "Unknown"

    # Find the game and check player's score
    for game in games:
        if "Indiana Pacers" in [game["HomeTeam"], game["AwayTeam"]] and "New York Knicks" in [game["HomeTeam"], game["AwayTeam"]]:
            game_id = game["GameID"]
            stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
            if not stats:
                # Fallback to proxy if primary fails
                stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
                if not stats:
                    return "Unknown"

            for stat in stats:
                if stat["Name"] == player_name:
                    points = stat["Points"]
                    return "Yes" if points > 20.5 else "No"
    return "No"

# Main function to resolve the market
def resolve_market():
    game_date = "2025-05-31"
    player_name = "Tyrese Haliburton"
    result = check_player_score(game_date, player_name)
    recommendation = RESOLUTION_MAP.get(result, "p3")
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    resolve_market()