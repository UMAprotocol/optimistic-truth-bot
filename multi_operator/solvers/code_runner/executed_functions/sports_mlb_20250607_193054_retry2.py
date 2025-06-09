import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data from both endpoints: {str(e)}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_formatted = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"/GamesByDate/{date_formatted}")

    if not games_today:
        return "recommendation: p4"

    for game in games_today:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: p1" if home_team == "Cubs" else "recommendation: p2"
                else:
                    return "recommendation: p2" if away_team == "Cubs" else "recommendation: p1"
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"
    return "recommendation: p4"

# Main execution logic
if __name__ == "__main__":
    game_date = "2025-06-07"
    home_team = "Tigers"
    away_team = "Cubs"
    print(determine_outcome(game_date, home_team, away_team))