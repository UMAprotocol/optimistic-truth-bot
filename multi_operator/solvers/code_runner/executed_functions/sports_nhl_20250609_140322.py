import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "MIN": "p2",  # Minnesota Timberwolves
    "OKC": "p1",  # Oklahoma City Thunder
    "Canceled": "p3",
    "Postponed": "p4",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == 'MIN' or game['AwayTeam'] == 'MIN':
            if game['HomeTeam'] == 'OKC' or game['AwayTeam'] == 'OKC':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return "recommendation: " + RESOLUTION_MAP[winner]
                elif game['Status'] == 'Canceled':
                    return "recommendation: " + RESOLUTION_MAP["Canceled"]
                elif game['Status'] == 'Postponed':
                    return "recommendation: " + RESOLUTION_MAP["Postponed"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_date = "2025-05-28"
    games = get_game_data(game_date)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print("recommendation: p4")