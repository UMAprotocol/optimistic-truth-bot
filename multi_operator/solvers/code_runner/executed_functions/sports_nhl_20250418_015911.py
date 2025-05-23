import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "WSH": "p2",  # Washington Capitals
    "PIT": "p1",  # Pittsburgh Penguins
    "50-50": "p3",
    "Too early to resolve": "p4",
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
        return "p4"  # No game data available

    if game['Status'] == "Canceled" and not game['Day']:
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Final":
        home_score = game['HomeTeamScore']
        away_score = game['AwayTeamScore']
        if home_score > away_score:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif away_score > home_score:
            return RESOLUTION_MAP[game['AwayTeam']]
    return "p4"  # Game not completed or postponed

def main():
    """
    Main function to determine the outcome of the NHL game.
    """
    game_date = "2025-04-17"
    team1 = "WSH"  # Washington Capitals
    team2 = "PIT"  # Pittsburgh Penguins

    game = fetch_nhl_game_data(game_date, team1, team2)
    resolution = resolve_market(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()