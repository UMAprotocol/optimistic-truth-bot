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
TEAM1 = "Los Angeles Dodgers"  # p1
TEAM2 = "New York Mets"        # p2
RESOLUTION_MAP = {
    "Dodgers": "p1",
    "Mets": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_resolve():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").date()
    # Check the game on the specified date and the next day (due to time zone differences)
    for date_shift in [0, 1]:
        game_date = date_formatted + timedelta(days=date_shift)
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date.strftime('%Y-%m-%d')}"
        games = make_request(url)
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
                        return "recommendation: " + RESOLUTION_MAP.get(winner, "p3")
                    elif game["Status"] in ["Canceled", "Postponed"]:
                        return "recommendation: p3"
                    else:
                        return "recommendation: p4"
    return "recommendation: p4"

# Main execution
if __name__ == "__main__":
    result = find_game_and_resolve()
    print(result)