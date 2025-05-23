import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIA": "p2",  # Miami Heat
    "ATL": "p1",  # Atlanta Hawks
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Miami Heat vs Atlanta Hawks game.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-18?key={NBA_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'MIA' and game['AwayTeam'] == 'ATL' or game['HomeTeam'] == 'ATL' and game['AwayTeam'] == 'MIA':
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Error fetching NBA game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # No game data found

    if game['Status'] == 'Final':
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == 'MIA':
            return "recommendation: p2"  # Miami Heat wins
        elif winner == 'ATL':
            return "recommendation: p1"  # Atlanta Hawks wins
    elif game['Status'] == 'Canceled':
        return "recommendation: p3"  # Game canceled, resolve 50-50
    elif game['Status'] == 'Postponed':
        return "recommendation: p4"  # Game postponed, too early to resolve

    return "recommendation: p4"  # Default case if none of the above conditions are met

def main():
    game_data = fetch_nba_game_data()
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()