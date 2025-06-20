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
HOME_TEAM = "Philadelphia Phillies"
AWAY_TEAM = "Atlanta Braves"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
        return "p4"  # Game not found, too early to resolve
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[HOME_TEAM]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[AWAY_TEAM]
        else:
            return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Postponed"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["Canceled"]
    else:
        return "p4"  # In progress or not started

def main():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games_data = get_data(games_url, HEADERS)
    
    if not games_data:
        # Try proxy if primary fails
        games_data = get_data(PROXY_ENDPOINT, HEADERS)
        if not games_data:
            print("Failed to retrieve data from both primary and proxy sources.")
            return

    game = find_game(games_data, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()