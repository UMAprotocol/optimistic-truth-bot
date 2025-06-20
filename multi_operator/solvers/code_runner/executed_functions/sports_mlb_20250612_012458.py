import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-11"
TEAM1 = "Detroit Tigers"
TEAM2 = "Baltimore Orioles"
RESOLUTION_MAP = {
    "Tigers": "p2",
    "Orioles": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_json_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(games, team1, team2):
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
           (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        home_runs = game['HomeTeamRuns']
        away_runs = game['AwayTeamRuns']
        if home_runs > away_runs:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif away_runs > home_runs:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
def main():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_json_response(url)
    if games is None:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
        return

    game = find_game(games, TEAM1, TEAM2)
    recommendation = resolve_market(game)
    print("recommendation:", recommendation)

if __name__ == "__main__":
    main()