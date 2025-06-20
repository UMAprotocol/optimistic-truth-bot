import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
RESOLUTION_MAP = {
    "SPI": "p2",  # Spirit
    "MOU": "p1",  # MOUZ
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_match_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    return None

def resolve_match(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeam']]
        else:
            return RESOLUTION_MAP["50-50"]
    elif game['Status'] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    match_date = "2025-06-19"
    team1 = "SPI"  # Spirit
    team2 = "MOU"  # MOUZ
    game_info = get_match_data(match_date, team1, team2)
    recommendation = resolve_match(game_info)
    print("recommendation:", recommendation)