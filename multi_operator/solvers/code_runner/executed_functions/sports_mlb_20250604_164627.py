import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2023-05-31"
TEAM1 = "LAA"  # Los Angeles Angels
TEAM2 = "CLE"  # Cleveland Guardians

# Function to make GET requests to the API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_outcome():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_data(url)
    if games is None:
        return "p4"  # Unable to fetch data

    for game in games:
        if game["HomeTeam"] == TEAM2 and game["AwayTeam"] == TEAM1:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p1"  # Guardians win
                elif game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return "p2"  # Angels win
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, check later
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled, resolve 50-50

    return "p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    result = find_game_and_outcome()
    print(f"recommendation: {result}")