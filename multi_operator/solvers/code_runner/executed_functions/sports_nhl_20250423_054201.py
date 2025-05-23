import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIN": "p2",  # Minnesota Wild
    "VGK": "p1",  # Vegas Golden Knights
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the Minnesota Wild vs. Vegas Golden Knights game.
    """
    date = "2025-04-22"
    team1 = "MIN"
    team2 = "VGK"
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
        logging.error(f"Error fetching NHL game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if game is None:
        return "recommendation: p4"

    if game['Status'] == "Canceled" and not game['Day']:
        return "recommendation: p3"
    elif game['Status'] == "Final":
        if game['HomeTeam'] == "MIN" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p2"
        elif game['AwayTeam'] == "MIN" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: p2"
        elif game['HomeTeam'] == "VGK" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p1"
        elif game['AwayTeam'] == "VGK" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: p1"
    return "recommendation: p4"

def main():
    game_data = fetch_nhl_game_data()
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()