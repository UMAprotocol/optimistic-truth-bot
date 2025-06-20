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
DATE = "2025-06-15"
TEAM1 = "San Diego Padres"  # Corresponds to p2
TEAM2 = "Arizona Diamondbacks"  # Corresponds to p1

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1: "p2",
    TEAM2: "p1",
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
def find_game_and_resolve():
    # Convert date to datetime object
    game_date = datetime.strptime(DATE, "%Y-%m-%d").date()
    # Check games on the exact date and the next day (to handle time zone issues)
    for offset in [0, 1]:
        date_to_check = game_date + timedelta(days=offset)
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_to_check}"
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
                        return "recommendation: " + RESOLUTION_MAP.get(winner, "p4")
                    elif game["Status"] in ["Canceled", "Postponed"]:
                        return "recommendation: p3"
                    else:
                        return "recommendation: p4"
    return "recommendation: p4"

# Main execution
if __name__ == "__main__":
    result = find_game_and_resolve()
    print(result)