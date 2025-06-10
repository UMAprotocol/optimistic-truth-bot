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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-nba-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "MIN": "p2",  # Timberwolves
    "OKC": "p1",  # Thunder
    "Postponed": "p4",
    "Canceled": "p3",
    "Scheduled": "p4"
}

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game(date_str):
    # Format the date and create the API path
    date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"GamesByDate/{date}"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, path)
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, path)
        if games is None:
            return "recommendation: p4"  # Unable to resolve

    # Search for the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {"MIN", "OKC"}:
            if game["Status"] == "Final":
                home_score = game["HomeTeamScore"]
                away_score = game["AwayTeamScore"]
                if home_score > away_score:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return f"recommendation: {RESOLUTION_MAP[winner]}"
            else:
                return f"recommendation: {RESOLUTION_MAP[game['Status']]}"
    
    return "recommendation: p4"  # Game not found or no final result

# Main execution function
if __name__ == "__main__":
    game_date = "2025-05-28"
    print(resolve_game(game_date))