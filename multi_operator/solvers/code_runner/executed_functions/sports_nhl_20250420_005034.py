import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "STL": "p2",  # St. Louis Blues
    "WPG": "p1",  # Winnipeg Jets
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

def fetch_nhl_game_data(game_date, team1, team2):
    """
    Fetches NHL game data for the specified teams and date.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching NHL game data: {e}")
        return None
    return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"
    if game['Status'] == "Canceled":
        return "recommendation: p3"
    elif game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        if winner == "STL":
            return "recommendation: p2"
        elif winner == "WPG":
            return "recommendation: p1"
    return "recommendation: p4"

def main():
    """
    Main function to determine the outcome of the NHL game.
    """
    game_date = "2025-04-19"
    team1 = "STL"
    team2 = "WPG"
    game = fetch_nhl_game_data(game_date, team1, team2)
    result = resolve_market(game)
    print(result)

if __name__ == "__main__":
    main()