import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "OTT": "p2",  # Ottawa Senators
    "TOR": "p1",  # Toronto Maple Leafs
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch NHL game data: {e}")
        return None

def determine_game_outcome(games, home_team, away_team):
    """
    Determines the outcome of the game based on the provided team abbreviations.
    """
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    game_date = "2025-04-20"
    home_team = "TOR"  # Toronto Maple Leafs
    away_team = "OTT"  # Ottawa Senators

    games = fetch_nhl_game_data(game_date)
    if games is None:
        print("recommendation: p4")
        return

    outcome = determine_game_outcome(games, home_team, away_team)
    print(f"recommendation: {outcome}")

if __name__ == "__main__":
    main()