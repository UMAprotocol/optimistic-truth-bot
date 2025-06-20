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
DATE = "2025-06-12"
TEAM1 = "Detroit Tigers"
TEAM2 = "Baltimore Orioles"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Detroit Tigers win
    TEAM2: "p1",  # Baltimore Orioles win
    "50-50": "p3",  # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
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
    # Convert date to the required format and check the day after as well
    game_date = datetime.strptime(DATE, "%Y-%m-%d").date()
    dates_to_check = [game_date, game_date + timedelta(days=1)]

    for date in dates_to_check:
        formatted_date = date.strftime("%Y-%m-%d")
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
        games = get_data(url)
        if games:
            for game in games:
                if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                    if game["Status"] == "Final":
                        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                            winner = game["HomeTeam"]
                        else:
                            winner = game["AwayTeam"]
                        return RESOLUTION_MAP.get(winner, "p4")
                    elif game["Status"] in ["Canceled", "Postponed"]:
                        return RESOLUTION_MAP["50-50"]
                    else:
                        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")