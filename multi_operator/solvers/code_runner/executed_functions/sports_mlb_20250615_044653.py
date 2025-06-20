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
GAME_DATE = "2025-06-14"
HOME_TEAM = "Mariners"
AWAY_TEAM = "Guardians"

# Resolution map
RESOLUTION_MAP = {
    "Mariners": "p1",
    "Guardians": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, home_team, away_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed, trying primary endpoint")
        games = response.json()
    except:
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            return None
        games = response.json()

    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        home_score = game["HomeTeamRuns"]
        away_score = game["AwayTeamRuns"]
        if home_score > away_score:
            return "recommendation: " + RESOLUTION_MAP[game["HomeTeam"]]
        elif away_score > home_score:
            return "recommendation: " + RESOLUTION_MAP[game["AwayTeam"]]
    elif game["Status"] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game["Status"] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game_info)
    print(result)