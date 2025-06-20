import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Date and teams for the game
GAME_DATE = "2025-06-15"
HOME_TEAM = "Rays"
AWAY_TEAM = "Mets"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Rays": "p2",
    "Mets": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p4"
}

def fetch_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        return None

def get_game_data(date, home_team, away_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = fetch_data(url)
    if games is None:
        print("Falling back to proxy endpoint.")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = fetch_data(url)
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No game data found
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return f"recommendation: {RESOLUTION_MAP[game['HomeTeam']]}"
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return f"recommendation: {RESOLUTION_MAP[game['AwayTeam']]}"
    elif game['Status'] == "Postponed":
        return "recommendation: p4"  # Game postponed, check later
    elif game['Status'] == "Canceled":
        return "recommendation: p3"  # Game canceled, resolve as 50-50
    return "recommendation: p4"  # Default case if none above match

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game_info)
    print(result)