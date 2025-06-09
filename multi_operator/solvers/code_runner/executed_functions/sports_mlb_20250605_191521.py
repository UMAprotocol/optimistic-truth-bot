import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Diamondbacks": "p2",
    "Braves": "p1",
    "Canceled": "p3",
    "Postponed": "p4",
    "Unknown": "p4"
}

# Function to get data from API
def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(game_data):
    if not game_data:
        return "p4"  # No data available
    status = game_data.get("Status")
    if status == "Final":
        home_team = game_data.get("HomeTeam")
        away_team = game_data.get("AwayTeam")
        home_score = game_data.get("HomeTeamRuns")
        away_score = game_data.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP.get(home_team, "Unknown")
        elif away_score > home_score:
            return RESOLUTION_MAP.get(away_team, "Unknown")
    elif status in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP.get(status)
    return "p4"

# Main function to process the game data
def process_game(date_str, home_team, away_team):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    games = get_data(url)
    if not games:
        print("Trying proxy endpoint...")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
        games = get_data(url)
    if games:
        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return determine_outcome(game)
    return "p4"

# Example usage
if __name__ == "__main__":
    game_date = "2025-06-05"
    home_team = "ATL"  # Atlanta Braves
    away_team = "ARI"  # Arizona Diamondbacks
    recommendation = process_game(game_date, home_team, away_team)
    print(f"recommendation: {recommendation}")