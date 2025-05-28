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
RESOLUTION_MAP = {
    "Rockies": "p2",
    "Cubs": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[home_team]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-27"
    home_team = "Cubs"
    away_team = "Rockies"
    games = get_game_data(game_date)
    if games:
        recommendation = resolve_market(games, home_team, away_team)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print(f"recommendation: {recommendation}")