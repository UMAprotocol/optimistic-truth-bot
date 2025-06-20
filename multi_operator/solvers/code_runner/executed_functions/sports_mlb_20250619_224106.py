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
DATE = "2025-06-19"
TEAM1 = "Cleveland Guardians"
TEAM2 = "San Francisco Giants"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

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
                    return resolve_game(game)
    return "p4"  # If no game is found or in progress

# Function to resolve the game based on its status
def resolve_game(game):
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        
        if winner == TEAM1:
            return "p2"  # Guardians win
        elif winner == TEAM2:
            return "p1"  # Giants win
    elif game["Status"] == "Canceled":
        return "p3"  # Game canceled
    elif game["Status"] == "Postponed":
        return "p4"  # Game postponed, check later
    return "p4"  # Default case, game not final or status unknown

# Main execution function
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")