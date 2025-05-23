import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MIN": "p2",  # Timberwolves win
    "LAL": "p1",  # Lakers win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Future or ongoing game
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nba_game_data(game_date):
    """
    Fetches NBA game data for a specific date.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logger.error(f"Error fetching NBA game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'MIN' and game['AwayTeam'] == 'LAL' or game['HomeTeam'] == 'LAL' and game['AwayTeam'] == 'MIN':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return f"recommendation: {RESOLUTION_MAP[winner]}"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return f"recommendation: {RESOLUTION_MAP['50-50']}"
            else:
                return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"
    return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"

def main():
    """
    Main function to determine the outcome of the NBA game between Timberwolves and Lakers.
    """
    game_date = "2025-04-22"
    games = fetch_nba_game_data(game_date)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print(f"recommendation: {RESOLUTION_MAP['Too early to resolve']}")

if __name__ == "__main__":
    main()