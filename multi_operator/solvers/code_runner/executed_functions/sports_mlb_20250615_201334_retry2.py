import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Angels": "p2",
    "Orioles": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"

    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except Exception:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            response.raise_for_status()

    games = response.json()
    for game in games:
        if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        home_team = game["HomeTeam"]
        away_team = game["AwayTeam"]
        home_score = game["HomeTeamRuns"]
        away_score = game["AwayTeamRuns"]
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team
        return "recommendation: " + RESOLUTION_MAP[winner]
    elif game["Status"] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game["Status"] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-15"
    team1 = "Los Angeles Angels"
    team2 = "Baltimore Orioles"

    game = get_game_data(game_date, team1, team2)
    result = resolve_market(game)
    print(result)