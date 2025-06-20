import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Game details
GAME_DATE = "2025-06-13"
TEAMS = {"Thunder": "OKC", "Pacers": "IND"}

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "OKC": "p2",  # Thunder win
    "IND": "p1",  # Pacers win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def analyze_game_data(games):
    """Analyze game data to determine the outcome."""
    for game in games:
        if game['Status'] == "Final":
            home_team = game['HomeTeam']
            away_team = game['AwayTeam']
            home_score = game['HomeTeamScore']
            away_score = game['AwayTeamScore']
            if home_score > away_score:
                return RESOLUTION_MAP.get(home_team, "Unknown")
            elif away_score > home_score:
                return RESOLUTION_MAP.get(away_team, "Unknown")
        elif game['Status'] in ["Postponed", "Canceled"]:
            return RESOLUTION_MAP.get(game['Status'])
    return "p4"  # No relevant game found or still in progress

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_data(games)
    else:
        recommendation = "p4"  # Unable to retrieve data
    print(f"recommendation: {recommendation}")