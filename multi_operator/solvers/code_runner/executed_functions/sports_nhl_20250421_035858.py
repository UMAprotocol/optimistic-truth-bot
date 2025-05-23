import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "GSW": "p2",  # Golden State Warriors win
    "HOU": "p1",  # Houston Rockets win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data(date, team1, team2):
    """
    Fetches NBA game data for the specified date and teams.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching NBA game data: {e}")
    return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # No data available

    if game['Status'] == "Scheduled":
        return "p4"  # Game has not yet been played
    elif game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        if winner == "GSW":
            return RESOLUTION_MAP["GSW"]
        elif winner == "HOU":
            return RESOLUTION_MAP["HOU"]
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "p3"  # Game canceled or postponed

    return "p3"  # Default to unresolved

def main():
    """
    Main function to determine the outcome of the NBA game between the Warriors and the Rockets.
    """
    date = "2025-04-20"
    team1 = "GSW"
    team2 = "HOU"
    game = fetch_nba_game_data(date, team1, team2)
    resolution = resolve_market(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()