import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "COL": "p2",  # Colorado Avalanche
    "DAL": "p1",  # Dallas Stars
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
        return "p4"  # No game data found

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        if winner == "COL":
            return RESOLUTION_MAP["COL"]
        elif winner == "DAL":
            return RESOLUTION_MAP["DAL"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to determine the outcome of the NHL game between Avalanche and Stars.
    """
    game_date = "2025-04-21"
    team1 = "COL"  # Colorado Avalanche
    team2 = "DAL"  # Dallas Stars

    game_data = fetch_nhl_game_data(game_date, team1, team2)
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()