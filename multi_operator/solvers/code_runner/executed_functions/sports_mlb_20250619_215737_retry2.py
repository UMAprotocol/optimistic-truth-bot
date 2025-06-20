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
    "Diamondbacks": "p2",
    "Blue Jays": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # Fallback to proxy if primary fails
        try:
            proxy_url = PROXY_ENDPOINT + url[len(PRIMARY_ENDPOINT):]
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve data from both primary and proxy endpoints: {e}")
            return None

def find_game(date, home_team, away_team):
    games = get_data(f"{PRIMARY_ENDPOINT}/GamesByDate/{date}")
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP["Blue Jays"]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP["Diamondbacks"]
    elif game['Status'] == 'Canceled':
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == 'Postponed':
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-19"
    home_team = "Blue Jays"
    away_team = "Diamondbacks"
    game = find_game(game_date, home_team, away_team)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")