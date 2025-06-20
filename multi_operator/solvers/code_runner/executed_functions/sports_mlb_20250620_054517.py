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

# Function to make GET requests to the API
def get_api_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_api_data(url)
    
    if games is None:
        return "p4"  # Unable to retrieve data

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p1" if game["HomeTeam"] == team1 else "p2"
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return "p2" if game["HomeTeam"] == team1 else "p1"
            elif game["Status"] == "Canceled":
                return "p3"
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, check later
    return "p4"  # No matching game found or game not yet played

# Main execution function
def main():
    date = "2025-06-19"
    team1 = "LAD"  # Los Angeles Dodgers
    team2 = "SD"   # San Diego Padres
    result = find_game_and_determine_outcome(date, team1, team2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()