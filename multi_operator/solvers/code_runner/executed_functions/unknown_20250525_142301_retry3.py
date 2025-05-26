import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to handle API requests
def get_data(url, retries=3, backoff=1.5):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                time.sleep(backoff * (2 ** attempt))
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise ConnectionError(f"API request failed after {retries} attempts: {e}")
    return None

# Function to find team keys
def find_team_keys():
    url = "https://api.sportsdata.io/v3/mlb/scores/json/Teams"
    teams = get_data(url)
    team_keys = {}
    for team in teams:
        team_keys[team["Name"]] = team["Key"]
    return team_keys

# Function to determine the game outcome
def determine_outcome(date, team1_key, team2_key):
    date_formatted = datetime.strptime(date, "%Y-%m-%d").date()
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_data(url)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1_key, team2_key}:
                if game["Status"] == "Final":
                    home_runs = game["HomeTeamRuns"]
                    away_runs = game["AwayTeamRuns"]
                    if home_runs > away_runs:
                        return "p1" if game["HomeTeam"] == team1_key else "p2"
                    elif away_runs > home_runs:
                        return "p1" if game["AwayTeam"] == team1_key else "p2"
                    else:
                        return "p3"  # Tie
                else:
                    return "p4"  # Game not final
    return "p4"  # No game found or other issues

# Main execution block
if __name__ == "__main__":
    date = "2025-04-23"
    team1 = "Texas Rangers"
    team2 = "Oakland Athletics"

    team_keys = find_team_keys()
    team1_key = team_keys.get(team1)
    team2_key = team_keys.get(team2)

    if not team1_key or not team2_key:
        print("One of the team keys could not be found.")
    else:
        result = determine_outcome(date, team1_key, team2_key)
        print(f"recommendation: {result}")