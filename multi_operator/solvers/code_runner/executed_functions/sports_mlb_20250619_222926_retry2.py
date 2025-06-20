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
    "Guardians": "p2",
    "Giants": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Function to find and resolve the game outcome
def resolve_game(date, home_team, away_team):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{date}")
    if not games:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    
    if not games:
        return "Too early to resolve"

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == 'Postponed':
                return "Too early to resolve"
    return "Too early to resolve"

# Main execution function
def main():
    date = "2025-06-19"
    home_team = "Giants"
    away_team = "Guardians"
    result = resolve_game(date, home_team, away_team)
    print(f"recommendation: {RESOLUTION_MAP.get(result, 'p4')}")

if __name__ == "__main__":
    main()