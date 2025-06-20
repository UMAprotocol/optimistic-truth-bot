import os
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-06-14"
TEAM1 = "Pittsburgh Pirates"
TEAM2 = "Chicago Cubs"

# Function to get data from API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {str(e)}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").date()
    games_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_data(games_url)

    if not games:
        return "p4"  # Unable to fetch data or no games found

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p1" if game["HomeTeam"] == TEAM1 else "p2"
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return "p2" if game["HomeTeam"] == TEAM1 else "p1"
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, check later
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled, resolve as 50-50
    return "p4"  # No matching game found or game not final

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")