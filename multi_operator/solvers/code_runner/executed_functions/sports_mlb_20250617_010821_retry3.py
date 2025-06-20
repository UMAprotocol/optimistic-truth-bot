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

# Game details
GAME_DATE = "2025-06-16"
HOME_TEAM = "Rockies"
AWAY_TEAM = "Nationals"

# Resolution map
RESOLUTION_MAP = {
    "Rockies": "p2",
    "Nationals": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

def get_game_data(date, home_team, away_team):
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
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No game data found

    if game["Status"] == "Final":
        home_score = game["HomeTeamRuns"]
        away_score = game["AwayTeamRuns"]
        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[game['HomeTeam']]}"
        else:
            return f"recommendation: {RESOLUTION_MAP[game['AwayTeam']]}"
    elif game["Status"] == "Postponed":
        return "recommendation: p4"  # Postponed games remain open
    elif game["Status"] == "Canceled":
        return "recommendation: p3"  # Canceled games resolve as 50-50

    return "recommendation: p4"  # Default case if none above match

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game_info)
    print(result)