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
DATE = "2025-06-15"
TEAM1 = "Toronto Blue Jays"
TEAM2 = "Philadelphia Phillies"
RESOLUTION_MAP = {
    "Blue Jays": "p2",
    "Phillies": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_games_by_date(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(games, team1, team2):
    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP["Blue Jays"]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return RESOLUTION_MAP["Phillies"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    games = get_games_by_date(DATE)
    if games:
        recommendation = resolve_market(games, TEAM1, TEAM2)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", recommendation)