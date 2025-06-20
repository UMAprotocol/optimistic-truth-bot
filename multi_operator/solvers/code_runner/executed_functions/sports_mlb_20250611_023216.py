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
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Constants
DATE = "2025-06-10"
TEAM1 = "Braves"
TEAM2 = "Brewers"

# Function to get data from API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").date()
    games_on_date_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_data(games_on_date_url)

    if games is None:
        return "p4"  # Unable to fetch data, cannot determine outcome

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p2" if game["HomeTeam"] == TEAM1 else "p1"
                else:
                    return "p1" if game["HomeTeam"] == TEAM2 else "p2"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"
            else:
                return "p4"  # Game not completed yet

    return "p4"  # No game found or game not yet played

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(f"recommendation: {result}")