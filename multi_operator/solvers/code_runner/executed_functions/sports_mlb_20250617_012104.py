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
DATE = "2025-06-16"
TEAM1 = "Washington Nationals"  # p1
TEAM2 = "Colorado Rockies"      # p2

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
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
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").date()
    # Check for the game on the specified date and the next day (to handle time zone issues)
    for offset in range(2):
        game_date = date_formatted + timedelta(days=offset)
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date.strftime('%Y-%m-%d')}"
        games = get_data(url)
        if games:
            for game in games:
                if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                    if game["Status"] == "Final":
                        home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                        away_team_wins = game["AwayTeamRuns"] > game["HomeTeamRuns"]
                        if home_team_wins:
                            return RESOLUTION_MAP[game["HomeTeam"]]
                        elif away_team_wins:
                            return RESOLUTION_MAP[game["AwayTeam"]]
                    elif game["Status"] in ["Canceled", "Postponed"]:
                        return RESOLUTION_MAP["50-50"]
                    else:
                        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")