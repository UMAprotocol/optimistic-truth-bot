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
GAME_DATE = "2025-06-07"
HOME_TEAM = "St. Louis Cardinals"
AWAY_TEAM = "Los Angeles Dodgers"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
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
        return "p4"  # Game not found, assume it's too early or in progress
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[HOME_TEAM]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP[AWAY_TEAM]
        else:
            return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["Canceled"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Postponed"]
    else:
        return "p4"  # In progress or other non-final status

def main():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = get_data(games_url)
    if not games:
        print("Failed to retrieve games data.")
        return

    game = find_game(games, HOME_TEAM, AWAY_TEAM)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()