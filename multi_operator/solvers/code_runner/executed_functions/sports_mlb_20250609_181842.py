import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Game details
GAME_DATE = "2025-05-30"
TEAMS = {"Twins": "p2", "Mariners": "p1"}

# Function to fetch data from API
def fetch_data(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Function to resolve the game outcome
def resolve_game(date, teams):
    date_formatted = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = fetch_data(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}") or fetch_data(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if not games_today:
        return "recommendation: p4"  # Unable to fetch data

    for game in games_today:
        if game["HomeTeam"] in teams and game["AwayTeam"] in teams:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                away_team_wins = game["AwayTeamRuns"] > game["HomeTeamRuns"]
                if home_team_wins:
                    return f"recommendation: {TEAMS[game['HomeTeam']]}"
                elif away_team_wins:
                    return f"recommendation: {TEAMS[game['AwayTeam']]}"
            elif game["Status"] == "Canceled":
                return "recommendation: p3"
            elif game["Status"] == "Postponed":
                return "recommendation: p4"
    return "recommendation: p4"

# Main execution
if __name__ == "__main__":
    result = resolve_game(GAME_DATE, TEAMS)
    print(result)