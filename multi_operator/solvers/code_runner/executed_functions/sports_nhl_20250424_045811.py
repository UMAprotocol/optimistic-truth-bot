import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "DAL": "p2",  # Dallas Stars
    "COL": "p1",  # Colorado Avalanche
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the Dallas Stars vs Colorado Avalanche game on April 23, 2025.
    """
    date = "2025-04-23"
    team1 = "DAL"  # Dallas Stars
    team2 = "COL"  # Colorado Avalanche
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
        return "recommendation: p4"  # No game data available

    if game['Status'] == "Canceled":
        return "recommendation: p3"  # Game canceled, resolve as 50-50
    elif game['Status'] == "Postponed":
        return "recommendation: p4"  # Game postponed, too early to resolve
    elif game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"  # Resolve based on winner
    else:
        return "recommendation: p4"  # Game not yet completed or other statuses

def main():
    """
    Main function to determine the resolution of the NHL game.
    """
    game_data = fetch_nhl_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()