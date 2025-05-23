import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "LAK": "p1",  # Los Angeles Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NHL game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    if games is None:
        return "recommendation: p4"

    for game in games:
        if game['HomeTeam'] == "EDM" or game['AwayTeam'] == "EDM":
            if game['HomeTeam'] == "LAK" or game['AwayTeam'] == "LAK":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    
                    return f"recommendation: {RESOLUTION_MAP.get(winner, 'p4')}"
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"
                else:
                    return "recommendation: p4"
    return "recommendation: p4"

def main():
    """
    Main function to determine the outcome of the Oilers vs. Kings game.
    """
    game_date = "2025-04-21"
    games = fetch_nhl_game_data(game_date)
    result = resolve_market(games)
    print(result)

if __name__ == "__main__":
    main()