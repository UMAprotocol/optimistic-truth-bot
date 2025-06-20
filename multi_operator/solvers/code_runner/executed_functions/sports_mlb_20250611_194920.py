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
DATE = "2025-06-11"
TEAM1 = "CIN"  # Cincinnati Reds
TEAM2 = "CLE"  # Cleveland Guardians
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to make API requests
def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    # Convert date to datetime object
    game_date = datetime.strptime(DATE, "%Y-%m-%d").date()

    # Check games on the specified date
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}"
    games = make_request(url)
    if games is None:
        return "recommendation: p4"  # Unable to fetch data

    # Find the specific game
    for game in games:
        if game["HomeTeam"] == TEAM2 and game["AwayTeam"] == TEAM1:
            if game["Status"] == "Final":
                # Determine the winner
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "recommendation: p1"  # Guardians win
                elif away_score > home_score:
                    return "recommendation: p2"  # Reds win
            elif game["Status"] == "Postponed":
                return "recommendation: p4"  # Game postponed
            elif game["Status"] == "Canceled":
                return "recommendation: p3"  # Game canceled

    # If no game found or other conditions
    return "recommendation: p4"

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(result)