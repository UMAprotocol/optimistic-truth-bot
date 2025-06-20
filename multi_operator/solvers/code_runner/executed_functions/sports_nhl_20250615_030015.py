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
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Matthew Tkachuk"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API URLs
PRIMARY_URL = "https://api.sportsdata.io/v3/nhl"
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, params):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to find and analyze the game
def analyze_game():
    date_str = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_URL}/scores/json/GamesByDate/{date_str}"
    games = make_request(url, {})

    if games is None:
        print("Failed to retrieve data from primary source, trying proxy...")
        games = make_request(PROXY_URL, {"date": date_str})

    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
                if game["Status"] == "Final":
                    return analyze_player_performance(game["GameId"])
                elif game["Status"] in ["Scheduled", "InProgress"]:
                    return "Too early to resolve"
                else:
                    return "50-50"
    return "50-50"

# Function to analyze player performance
def analyze_player_performance(game_id):
    url = f"{PRIMARY_URL}/stats/json/PlayerGameStatsByGame/{game_id}"
    player_stats = make_request(url, {})

    if player_stats:
        for stat in player_stats:
            if stat["Name"] == PLAYER_NAME:
                goals = stat.get("Goals", 0)
                return "Yes" if goals > 0.5 else "No"
    return "No"

# Main execution function
if __name__ == "__main__":
    result = analyze_game()
    recommendation = RESOLUTION_MAP.get(result, "p4")
    print(f"recommendation: {recommendation}")