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
GAME_DATE = "2025-05-28"
HOME_TEAM = "Cleveland Guardians"
AWAY_TEAM = "Los Angeles Dodgers"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
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
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return HOME_TEAM
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return AWAY_TEAM
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "50-50"
    return "Too early to resolve"

def main():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = get_data(games_url)
    
    if not games:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
        return
    
    game = find_game(games, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game)
    print("recommendation:", RESOLUTION_MAP.get(result, "p4"))

if __name__ == "__main__":
    main()