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

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Function to perform HTTP GET requests
def get_data(url, tag):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching data for {tag}: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game(date_str, team1, team2):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    games = get_data(url, "GamesByDate")
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        return "p2" if game["HomeTeam"] == team1 else "p1"
                    else:
                        return "p1" if game["HomeTeam"] == team1 else "p2"
                elif game["Status"] == "Canceled":
                    return "p3"
                elif game["Status"] == "Postponed":
                    return "p4"
    return "p4"

# Main function to run the resolver
def main():
    date = "2025-05-28"
    team1 = "MIL"  # Milwaukee Brewers
    team2 = "BOS"  # Boston Red Sox
    result = resolve_game(date, team1, team2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()