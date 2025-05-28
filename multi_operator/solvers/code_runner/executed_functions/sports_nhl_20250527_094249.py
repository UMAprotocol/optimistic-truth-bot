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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Team abbreviations and resolution map
TEAMS = {
    "Carolina Hurricanes": "CAR",
    "Florida Panthers": "FLA"
}
RESOLUTION_MAP = {
    "CAR": "p2",  # Hurricanes win
    "FLA": "p1",  # Panthers win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game(date_str):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/GamesByDate/{formatted_date}")
    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"/GamesByDate/{formatted_date}")
    
    if games_today:
        for game in games_today:
            if game["HomeTeam"] in TEAMS.values() and game["AwayTeam"] in TEAMS.values():
                if game["Status"] == "Final":
                    if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        return "recommendation: " + RESOLUTION_MAP[game["HomeTeam"]]
                    else:
                        return "recommendation: " + RESOLUTION_MAP[game["AwayTeam"]]
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"
    return "recommendation: p4"

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-26"
    print(resolve_game(game_date))