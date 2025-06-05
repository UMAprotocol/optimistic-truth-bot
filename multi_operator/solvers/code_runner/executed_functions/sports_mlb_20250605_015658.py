import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-04"
TEAM1 = "New York Yankees"  # p1
TEAM2 = "Cleveland Guardians"  # p2

# Resolution map
RESOLUTION_MAP = {
    "Yankees": "p1",
    "Guardians": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to get data from API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    # Convert date to datetime object
    game_date = datetime.strptime(DATE, "%Y-%m-%d").date()

    # Check games on the specified date and the next day (to handle time zone issues)
    for offset in range(2):
        date_to_check = game_date + timedelta(days=offset)
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_to_check.strftime('%Y-%m-%d')}"
        games = get_data(url)
        if games:
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
                    elif game["Status"] in ["Canceled", "Postponed"]:
                        return "p3"
                    else:
                        return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")