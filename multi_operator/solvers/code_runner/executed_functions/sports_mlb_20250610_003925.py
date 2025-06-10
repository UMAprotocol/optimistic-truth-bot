import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Yankees": "p2",
    "Dodgers": "p1",
    "50-50": "p3"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Function to find game and determine outcome
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")
    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")
    
    if games_today:
        for game in games_today:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        winner = game["HomeTeam"]
                    else:
                        winner = game["AwayTeam"]
                    return RESOLUTION_MAP.get(winner, "p3")
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return "p3"
                else:
                    return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-01"
    home_team = "Dodgers"
    away_team = "Yankees"
    result = resolve_game(game_date, home_team, away_team)
    print(f"recommendation: {result}")