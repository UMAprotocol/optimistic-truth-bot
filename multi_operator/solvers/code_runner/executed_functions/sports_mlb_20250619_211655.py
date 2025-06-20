import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-19"
TEAM1 = "White Sox"
TEAM2 = "Cardinals"
GAME_DATE_FORMAT = "%Y-%m-%d"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "White Sox": "p1",
    "Cardinals": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_games_by_date(date):
    """Fetch games by date from the MLB API."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(games, team1, team2):
    """Resolve the market based on the game outcome."""
    for game in games:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return "recommendation: " + RESOLUTION_MAP[winner]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled on the same day
                rescheduled_games = get_games_by_date(datetime.strptime(game['Day'], GAME_DATE_FORMAT).strftime('%Y-%m-%d'))
                if rescheduled_games:
                    return resolve_market(rescheduled_games, team1, team2)
                else:
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_games_by_date(DATE)
    if games:
        result = resolve_market(games, TEAM1, TEAM2)
    else:
        result = "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    print(result)