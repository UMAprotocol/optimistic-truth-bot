import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Team abbreviations
TEAMS = {
    "Oilers": "EDM",
    "Stars": "DAL"
}

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "EDM": "p2",  # Oilers win
    "DAL": "p1",  # Stars win
    "50-50": "p3",  # Game canceled
    "Too early to resolve": "p4"  # Game not yet played or in progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_game_results(games):
    """Analyze game results to determine the outcome."""
    for game in games:
        if game['Status'] == "Final":
            home_team = game['HomeTeam']
            away_team = game['AwayTeam']
            home_score = game['HomeTeamScore']
            away_score = game['AwayTeamScore']
            if home_score > away_score:
                return RESOLUTION_MAP.get(home_team, "Too early to resolve")
            elif away_score > home_score:
                return RESOLUTION_MAP.get(away_team, "Too early to resolve")
        elif game['Status'] in ["Canceled", "Postponed"]:
            return "p3"  # Game not completed or canceled
    return "p4"  # No final or relevant game found

def main():
    game_date = "2025-05-29"
    games = get_game_data(game_date)
    if games:
        result = analyze_game_results(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to retrieve data

if __name__ == "__main__":
    main()