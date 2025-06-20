import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API access
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "YES": "p2",  # Brad Marchand scores a goal
    "NO": "p1",   # Brad Marchand does not score a goal
    "UNKNOWN": "p3"  # Game not completed or data unavailable
}

# Function to fetch data from API
def fetch_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check if Brad Marchand scored a goal
def check_goal(game_id):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    data = fetch_data(url, HEADERS)
    if data:
        for player in data:
            if player["Name"] == "Brad Marchand":
                goals = player.get("Goals", 0)
                return "YES" if goals > 0 else "NO"
    return "UNKNOWN"

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-12"
    teams = ["Edmonton Oilers", "Florida Panthers"]
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = fetch_data(url, HEADERS)
    if games:
        for game in games:
            if game["HomeTeam"] in teams and game["AwayTeam"] in teams:
                game_status = game["Status"]
                if game_status == "Final":
                    result = check_goal(game["GameID"])
                    return f"recommendation: {RESOLUTION_MAP[result]}"
                else:
                    return "recommendation: p3"  # Game not completed
    return "recommendation: p3"  # No data or game not found

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())