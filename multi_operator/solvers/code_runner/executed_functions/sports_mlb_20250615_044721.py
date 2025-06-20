import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-14"
TEAM1 = "SF"  # San Francisco Giants
TEAM2 = "LAD"  # Los Angeles Dodgers

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
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_data(url)
    
    if games is None:
        return "p4"  # Unable to fetch data, consider as unresolved

    for game in games:
        if game["HomeTeam"] == TEAM2 and game["AwayTeam"] == TEAM1:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "p1"  # Dodgers win
                elif away_score > home_score:
                    return "p2"  # Giants win
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, unresolved
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled, resolve as 50-50
    return "p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")