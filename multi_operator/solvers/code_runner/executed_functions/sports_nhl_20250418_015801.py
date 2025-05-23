import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "CAR": "p2",  # Carolina Hurricanes
    "OTT": "p1",  # Ottawa Senators
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the Hurricanes vs Senators game on the specified date.
    """
    date = "2025-04-17"
    team1 = "CAR"  # Carolina Hurricanes
    team2 = "OTT"  # Ottawa Senators
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={NHL_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or \
               game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching NHL game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # No game data available

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "CAR":
            return RESOLUTION_MAP["CAR"]
        elif winner == "OTT":
            return RESOLUTION_MAP["OTT"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open

    return "p4"  # Default case if none of the above conditions are met

def main():
    game_data = fetch_nhl_game_data()
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()