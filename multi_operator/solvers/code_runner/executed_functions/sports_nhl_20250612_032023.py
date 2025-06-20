import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-06-11"
TEAM1 = "OKC"  # Oklahoma City Thunder
TEAM2 = "IND"  # Indiana Pacers

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Thunder win
    TEAM2: "p1",  # Pacers win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/nba/scores/json/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def analyze_game_results(games, team1, team2):
    """Analyze game results to determine the outcome."""
    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or \
           game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
            if game['Status'] == "Final":
                if game['HomeTeam'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return RESOLUTION_MAP[team1]
                elif game['HomeTeam'] == team2 and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return RESOLUTION_MAP[team2]
                else:
                    return "p3"  # Tie or error in data, resolve as 50-50
            else:
                return RESOLUTION_MAP.get(game['Status'], "p4")  # Postponed, Canceled, or Unknown
    return "p4"  # No game found or in-progress

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_results(games, TEAM1, TEAM2)
    else:
        recommendation = "p4"  # Unable to retrieve data
    print(f"recommendation: {recommendation}")