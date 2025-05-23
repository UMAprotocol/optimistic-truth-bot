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
GAME_DATE = "2025-05-22"
HOME_TEAM = "Pirates"
AWAY_TEAM = "Brewers"

# Resolution map
RESOLUTION_MAP = {
    "Pirates": "p1",
    "Brewers": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
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
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == 'Canceled':
        return "p3"  # Game canceled, resolve as 50-50
    elif game['Status'] == 'Postponed':
        return "p4"  # Game postponed, too early to resolve
    return "p4"  # Default case, game not yet completed or other status

def main():
    # Construct URL for the game date
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}"
    games = get_data(url, HEADERS)
    if not games:
        # Try proxy if primary fails
        games = get_data(PROXY_ENDPOINT, HEADERS)
    
    if games:
        game = find_game(games, HOME_TEAM, AWAY_TEAM)
        recommendation = resolve_market(game)
    else:
        recommendation = "p4"  # Unable to fetch data

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()