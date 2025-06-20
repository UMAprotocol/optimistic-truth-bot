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
GAME_DATE = "2025-06-10"
TEAMS = {"Dodgers": "Los Angeles Dodgers", "Padres": "San Diego Padres"}

# Resolution map
RESOLUTION_MAP = {
    "Dodgers": "p2",
    "Padres": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/mlb/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return RESOLUTION_MAP[home_team] if home_team in TEAMS.values() else RESOLUTION_MAP["50-50"]
        elif away_score > home_score:
            return RESOLUTION_MAP[away_team] if away_team in TEAMS.values() else RESOLUTION_MAP["50-50"]
        else:
            return RESOLUTION_MAP["50-50"]
    elif game['Status'] in ['Canceled', 'Postponed']:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_date_str = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    game_info = get_game_data(game_date_str)
    recommendation = resolve_market(game_info)
    print(f"recommendation: {recommendation}")