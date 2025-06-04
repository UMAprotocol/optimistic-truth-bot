import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Reds": "p2",
    "Cubs": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game(date, home_team, away_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if games is None:
        print("Using proxy endpoint due to primary endpoint failure.")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
        if games is None:
            return "recommendation: p4"  # Unable to resolve due to API failure

    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return f"recommendation: {RESOLUTION_MAP[home_team]}"
                elif away_score > home_score:
                    return f"recommendation: {RESOLUTION_MAP[away_team]}"
            elif game["Status"] == "Postponed":
                return "recommendation: p4"  # Game postponed, check later
            elif game["Status"] == "Canceled":
                return "recommendation: p3"  # Game canceled, resolve as 50-50
    return "recommendation: p4"  # No matching game found or in-progress

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-01"
    home_team = "Cubs"
    away_team = "Reds"
    result = resolve_game(game_date, home_team, away_team)
    print(result)