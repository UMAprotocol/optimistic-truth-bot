import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "ORL": "p2",  # Orlando Magic
    "BOS": "p1",  # Boston Celtics
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data(game_date, home_team, away_team):
    """
    Fetches NBA game data for the specified date and teams.
    """
    primary_url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={NBA_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-proxy/nba/GamesByDate/{game_date}?key={NBA_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # No game data found

    if game['Status'] == "Canceled":
        return "recommendation: p3"  # Game canceled, resolve 50-50
    elif game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p4')}"
    else:
        return "recommendation: p4"  # Game not completed or postponed

def main():
    """
    Main function to determine the outcome of the NBA game between Orlando Magic and Boston Celtics.
    """
    game_date = "2025-04-23"
    home_team = "BOS"  # Boston Celtics
    away_team = "ORL"  # Orlando Magic

    game_data = fetch_nba_game_data(game_date, home_team, away_team)
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()