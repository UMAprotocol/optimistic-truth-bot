import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "NYI": "p2",  # New York Islanders
    "CBJ": "p1",  # Columbus Blue Jackets
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the Islanders vs. Blue Jackets game.
    """
    date = "2025-04-17"
    team1 = "NYI"
    team2 = "CBJ"
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={NHL_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "NYI":
            return "recommendation: " + RESOLUTION_MAP["NYI"]
        elif winner == "CBJ":
            return "recommendation: " + RESOLUTION_MAP["CBJ"]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    game_data = fetch_nhl_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()