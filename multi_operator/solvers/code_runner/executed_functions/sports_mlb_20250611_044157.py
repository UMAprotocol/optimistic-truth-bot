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
def get_request(url, tag):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log.error(f"Error during {tag}: {str(e)}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_request(url, "GamesByDate")

    if games is None:
        return "p4"  # Unable to retrieve data

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p2" if game["HomeTeam"] == team1 else "p1"
                else:
                    return "p1" if game["AwayTeam"] == team1 else "p2"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"
            else:
                return "p4"  # Game not completed yet

    return "p4"  # No matching game found or game not yet played

# Main execution function
def main():
    date = "2025-06-10"
    team1 = "SD"  # San Diego Padres
    team2 = "LAD"  # Los Angeles Dodgers

    recommendation = find_game_and_determine_outcome(date, team1, team2)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()