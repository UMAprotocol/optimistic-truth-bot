import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Date and teams for the game
GAME_DATE = "2025-06-15"
TEAM1 = "Boston Red Sox"
TEAM2 = "New York Yankees"

# Function to get data from the API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_outcome():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").date()
    # Check the game date and the next day in case of timezone issues
    for date in [date_formatted, date_formatted + timedelta(days=1)]:
        url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
        games = get_data(url)
        if games:
            for game in games:
                if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                    if game["Status"] == "Final":
                        home_runs = game["HomeTeamRuns"]
                        away_runs = game["AwayTeamRuns"]
                        if home_runs > away_runs:
                            return "p1" if game["HomeTeam"] == TEAM1 else "p2"
                        elif away_runs > home_runs:
                            return "p2" if game["AwayTeam"] == TEAM2 else "p1"
                    elif game["Status"] == "Canceled":
                        return "p3"
                    elif game["Status"] == "Postponed":
                        # Market remains open, no resolution yet
                        return "p4"
    return "p4"  # If no game is found or it's still scheduled

# Main function to run the program
if __name__ == "__main__":
    result = find_game_and_outcome()
    print(f"recommendation: {result}")