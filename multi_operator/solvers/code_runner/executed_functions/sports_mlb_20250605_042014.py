import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-04"
TEAM1 = "Detroit Tigers"
TEAM2 = "Chicago White Sox"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Detroit Tigers win
    TEAM2: "p1",  # Chicago White Sox win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "50-50": "p3"  # Game canceled with no make-up
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def analyze_game(games):
    """Analyze game data to determine the outcome."""
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                home_runs = game["HomeTeamRuns"]
                away_runs = game["AwayTeamRuns"]
                if home_runs > away_runs:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p4")
            elif game["Status"] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game["Status"]]
    return "p4"  # No relevant game found or game not yet played

def main():
    """Main function to resolve the MLB game outcome."""
    try:
        games = get_game_data(GAME_DATE)
        recommendation = analyze_game(games)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()