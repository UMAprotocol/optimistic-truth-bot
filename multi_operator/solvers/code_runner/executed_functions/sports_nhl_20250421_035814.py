import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "GSW": "p2",  # Golden State Warriors
    "HOU": "p1",  # Houston Rockets
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

def fetch_nba_game_data(date):
    """
    Fetches NBA game data for the specified date.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logger.error(f"Failed to fetch NBA game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'GSW' and game['AwayTeam'] == 'HOU' or game['HomeTeam'] == 'HOU' and game['AwayTeam'] == 'GSW':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                return f"recommendation: {RESOLUTION_MAP[winner]}"
            elif game['Status'] == 'Canceled':
                return f"recommendation: {RESOLUTION_MAP['50-50']}"
            elif game['Status'] == 'Postponed':
                return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"
    return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"

def main():
    """
    Main function to determine the outcome of the NBA game between Warriors and Rockets.
    """
    date = "2025-04-20"
    games = fetch_nba_game_data(date)
    if games is None:
        print(f"recommendation: {RESOLUTION_MAP['Too early to resolve']}")
    else:
        result = resolve_market(games)
        print(result)

if __name__ == "__main__":
    main()