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

# Constants
DATE = "2025-06-11"
TEAM1 = "Texas Rangers"
TEAM2 = "Minnesota Twins"

# Resolution map
RESOLUTION_MAP = {
    "Rangers": "p2",
    "Twins": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_json_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_json_response(url)
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 or game['AwayTeam'] == team1) and \
               (game['HomeTeam'] == team2 or game['AwayTeam'] == team2):
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        home_runs = game['HomeTeamRuns']
        away_runs = game['AwayTeamRuns']
        if home_runs > away_runs:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        if winner == TEAM1.strip().split()[-1]:
            return RESOLUTION_MAP["Rangers"]
        else:
            return RESOLUTION_MAP["Twins"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game = find_game(DATE, TEAM1, TEAM2)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")