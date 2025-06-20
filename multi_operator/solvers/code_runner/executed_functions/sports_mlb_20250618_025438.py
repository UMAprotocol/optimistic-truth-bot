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
DATE = "2025-06-17"
TEAM1 = "New York Mets"
TEAM2 = "Atlanta Braves"
RESOLUTION_MAP = {
    "Mets": "p2",
    "Braves": "p1",
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
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            return game
    return None

def resolve_game_status(game):
    if game["Status"] == "Final":
        home_runs = game["HomeTeamRuns"]
        away_runs = game["AwayTeamRuns"]
        if home_runs > away_runs:
            return RESOLUTION_MAP["Mets"] if game["HomeTeam"] == "NYM" else RESOLUTION_MAP["Braves"]
        else:
            return RESOLUTION_MAP["Braves"] if game["AwayTeam"] == "ATL" else RESOLUTION_MAP["Mets"]
    elif game["Status"] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game["Status"] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
def main():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_json_response(url)
    
    if not games:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
        return
    
    game = find_game(games, "NYM", "ATL")
    if not game:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
        return
    
    result = resolve_game_status(game)
    print("recommendation:", result)

if __name__ == "__main__":
    main()