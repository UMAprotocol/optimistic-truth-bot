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

# Constants
DATE = "2025-06-15"
TEAM1 = "Pittsburgh Pirates"  # Corresponds to p2
TEAM2 = "Chicago Cubs"        # Corresponds to p1

# Helper functions
def get_json_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {str(e)}")
        return None

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_json_response(url)
    if games is None:
        return None, "p4"  # Unable to fetch data, consider as too early to resolve

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_runs = game["HomeTeamRuns"]
                away_runs = game["AwayTeamRuns"]
                if home_runs > away_runs:
                    return game, "p1" if game["HomeTeam"] == team2 else "p2"
                elif away_runs > home_runs:
                    return game, "p1" if game["AwayTeam"] == team2 else "p2"
            elif game["Status"] == "Canceled":
                return game, "p3"
            elif game["Status"] == "Postponed":
                return game, "p4"  # Postponed, check later
    return None, "p4"  # No game found or not final, consider as too early to resolve

# Main execution
if __name__ == "__main__":
    game_info, recommendation = find_game(DATE, TEAM1, TEAM2)
    print(f"recommendation: {recommendation}")