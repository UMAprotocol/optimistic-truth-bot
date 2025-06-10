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

# Resolution map
RESOLUTION_MAP = {
    "White Sox": "p2",
    "Orioles": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_game_data(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Failed to fetch data from primary endpoint, trying proxy.")
    except:
        response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}", headers=HEADERS, timeout=10)
        if not response.ok:
            return None

    games = response.json()
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        home_team = game['HomeTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return RESOLUTION_MAP[home_team]
        else:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == 'Canceled':
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == 'Postponed':
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-31"
    team1 = "Chicago White Sox"
    team2 = "Baltimore Orioles"
    game_info = get_game_data(game_date, team1, team2)
    recommendation = resolve_market(game_info)
    print(f"recommendation: {recommendation}")