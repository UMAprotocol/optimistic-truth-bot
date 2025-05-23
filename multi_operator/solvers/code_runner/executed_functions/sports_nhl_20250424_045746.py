import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "DAL": "p2",  # Dallas Stars win
    "COL": "p1",  # Colorado Avalanche win
    "50-50": "p3",  # Game canceled with no make-up
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.error(f"Error fetching NHL game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # No data available or game not found

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        return RESOLUTION_MAP.get(winner, "p4")
    elif game['Status'] == "Canceled":
        return "p3"  # Game canceled with no make-up
    elif game['Status'] == "Postponed":
        return "p4"  # Game postponed, market remains open

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to determine the outcome of the NHL game between Dallas Stars and Colorado Avalanche.
    """
    game_date = "2025-04-23"
    team1 = "DAL"  # Dallas Stars
    team2 = "COL"  # Colorado Avalanche

    game_data = fetch_nhl_game_data(game_date, team1, team2)
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()