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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Date and teams for the query
DATE = "2025-06-19"
TEAM1 = "Felix Auger-Aliassime"
TEAM2 = "Karen Khachanov"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Auger-Aliassime wins
    TEAM2: "p1",  # Khachanov wins
    "50-50": "p3",  # Tie, canceled, or delayed
    "Too early to resolve": "p4"  # Not enough data
}

def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def find_match(games, team1, team2):
    for game in games:
        participants = {game['HomeTeam'], game['AwayTeam']}
        if team1 in participants and team2 in participants:
            return game
    return None

def resolve_match(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return RESOLUTION_MAP.get(winner, "50-50")
    elif game['Status'] in ['Canceled', 'Postponed']:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    # Construct URL for the primary data source
    url = PRIMARY_ENDPOINT + DATE
    games = get_data(url)
    if not games:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games = get_data(PROXY_ENDPOINT)
    
    if games:
        match = find_match(games, TEAM1, TEAM2)
        result = resolve_match(match)
    else:
        result = RESOLUTION_MAP["Too early to resolve"]
    
    print("recommendation:", result)

if __name__ == "__main__":
    main()