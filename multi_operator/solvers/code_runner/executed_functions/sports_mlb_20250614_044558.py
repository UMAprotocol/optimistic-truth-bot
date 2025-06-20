import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-06-13"
TEAM1 = "Los Angeles Dodgers"  # p1
TEAM2 = "San Francisco Giants"  # p2

# Helper functions
def get_json_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_json_response(url)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                return game
    return None

def resolve_market(game):
    if not game:
        return "p3"  # Assume 50-50 if no game data found
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            return "p1" if game["HomeTeam"] == TEAM1 else "p2"
        else:
            return "p2" if game["AwayTeam"] == TEAM2 else "p1"
    elif game["Status"] in ["Canceled", "Postponed"]:
        return "p3"  # 50-50 for canceled or postponed
    return "p4"  # Game not yet played or in progress

# Main execution
if __name__ == "__main__":
    game = find_game(DATE, TEAM1, TEAM2)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")