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
DATE = "2025-06-17"
TEAM1 = "Philadelphia Phillies"
TEAM2 = "Miami Marlins"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Phillies win
    TEAM2: "p1",  # Marlins win
    "50-50": "p3",  # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Helper functions
def get_json_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game_by_date(team1, team2, date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_json_response(url)
    if games:
        for game in games:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
                return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return "recommendation: " + RESOLUTION_MAP[winner]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game = find_game_by_date(TEAM1, TEAM2, DATE)
    result = resolve_market(game)
    print(result)