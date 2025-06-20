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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map
RESOLUTION_MAP = {
    "Angels": "p2",
    "Orioles": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
}

# Helper functions
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def find_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[game['HomeTeam']]
        else:
            return "recommendation: " + RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == "Canceled":
        return "recommendation: p3"
    elif game['Status'] == "Postponed":
        return "recommendation: p4"
    return "recommendation: p4"

# Main execution
def main():
    date_str = "2025-06-15"
    home_team = "Orioles"
    away_team = "Angels"

    # Try proxy endpoint first
    games = get_data(f"{PROXY_ENDPOINT}/GamesByDate/{date_str}")
    if not games:
        # Fallback to primary endpoint
        games = get_data(f"{PRIMARY_ENDPOINT}/GamesByDate/{date_str}")

    if games:
        game = find_game(games, home_team, away_team)
        result = resolve_market(game)
    else:
        result = "recommendation: p4"

    print(result)

if __name__ == "__main__":
    main()