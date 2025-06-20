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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Yankees": "p2",
    "Royals": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, home_team, away_team):
    """ Fetch game data from the API """
    date_str = date.strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_str}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy endpoint
        proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date_str}"
        try:
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                    return game
        except requests.exceptions.RequestException:
            print("Error fetching data from proxy endpoint.")
    return None

def resolve_market(game):
    """ Determine the market resolution based on game data """
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[game['HomeTeam']]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == 'Canceled':
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == 'Postponed':
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Game details
    game_date = datetime.strptime("2025-06-11 19:40", "%Y-%m-%d %H:%M")
    home_team = "Royals"
    away_team = "Yankees"

    # Fetch game data and resolve the market
    game_info = get_game_data(game_date, home_team, away_team)
    result = resolve_market(game_info)
    print(result)