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
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nhl_game_data(game_date, team1, team2):
    """
    Fetches NHL game data for the specified date and teams.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching NHL game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # Too early to resolve or no data

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "STL":
            return "recommendation: p2"  # Blues win
        elif winner == "WPG":
            return "recommendation: p1"  # Jets win
    elif game['Status'] == "Canceled":
        return "recommendation: p3"  # Game canceled, resolve 50-50
    elif game['Status'] == "Postponed":
        return "recommendation: p4"  # Game postponed, too early to resolve

    return "recommendation: p4"  # Default case if none of the above conditions are met

def main():
    game_date = "2025-04-19"
    team1 = "STL"  # St. Louis Blues
    team2 = "WPG"  # Winnipeg Jets
    game = fetch_nhl_game_data(game_date, team1, team2)
    result = resolve_market(game)
    print(result)

if __name__ == "__main__":
    main()