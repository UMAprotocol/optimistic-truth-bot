import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "OTT": "p2",  # Ottawa Senators
    "TOR": "p1",  # Toronto Maple Leafs
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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
    except requests.RequestException as e:
        logger.error(f"Error fetching NHL game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    if games is None:
        return "recommendation: p4"

    for game in games:
        if game['HomeTeam'] == 'OTT' and game['AwayTeam'] == 'TOR' or game['HomeTeam'] == 'TOR' and game['AwayTeam'] == 'OTT':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                return f"recommendation: {RESOLUTION_MAP.get(winner, 'p4')}"
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"
            else:
                return "recommendation: p4"
    return "recommendation: p4"

def main():
    """
    Main function to determine the outcome of the NHL game between Senators and Maple Leafs.
    """
    game_date = "2025-04-22"
    games = fetch_nhl_game_data(game_date)
    result = resolve_market(games)
    print(result)

if __name__ == "__main__":
    main()