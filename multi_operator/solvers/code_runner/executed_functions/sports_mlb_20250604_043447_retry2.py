import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Padres": "p2",
    "Giants": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

# Helper function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Function to determine the outcome of the game
def resolve_game(date, home_team, away_team):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{date}")
    if not games:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    
    if not games:
        return "recommendation: p4"  # Unable to fetch data

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return f"recommendation: {RESOLUTION_MAP[home_team]}"
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return f"recommendation: {RESOLUTION_MAP[away_team]}"
            elif game['Status'] == "Postponed":
                return f"recommendation: {RESOLUTION_MAP['Postponed']}"
            elif game['Status'] == "Canceled":
                return f"recommendation: {RESOLUTION_MAP['Canceled']}"
    
    return "recommendation: p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-03"
    home_team = "Giants"
    away_team = "Padres"
    print(resolve_game(game_date, home_team, away_team))