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
    "Blue Jays": "p1",
    "Diamondbacks": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(date, home_team, away_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today_url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = get_data(games_today_url)
    if not games:
        games_today_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = get_data(games_today_url)
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP["Blue Jays"]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP["Diamondbacks"]
    elif game['Status'] == 'Canceled':
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == 'Postponed':
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_date = "2025-06-17"
    home_team = "TOR"  # Toronto Blue Jays
    away_team = "ARI"  # Arizona Diamondbacks
    game = find_game(game_date, home_team, away_team)
    result = resolve_market(game)
    print(result)