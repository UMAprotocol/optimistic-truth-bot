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
TEAM1 = "Houston Astros"  # p1
TEAM2 = "Chicago White Sox"  # p2

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to get data from the API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").date()
    games_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games_data = get_data(games_url)

    if games_data:
        for game in games_data:
            if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                if game["Status"] == "Final":
                    home_runs = game["HomeTeamRuns"]
                    away_runs = game["AwayTeamRuns"]
                    if home_runs > away_runs:
                        winner = game["HomeTeam"]
                    else:
                        winner = game["AwayTeam"]
                    return RESOLUTION_MAP.get(winner, "p3")
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return "p3"
                else:
                    return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")