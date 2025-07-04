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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-06-17"
HOME_TEAM = "Athletics"
AWAY_TEAM = "Astros"

# Resolution map
RESOLUTION_MAP = {
    "Athletics": "p1",
    "Astros": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return "Too early to resolve"
    if game['Status'] == 'Final':
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return HOME_TEAM
        elif away_score > home_score:
            return AWAY_TEAM
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "50-50"
    return "Too early to resolve"

def main():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = get_data(games_url)
    if games:
        game = find_game(games, HOME_TEAM, AWAY_TEAM)
        outcome = resolve_market(game)
        recommendation = RESOLUTION_MAP.get(outcome, "p4")
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()