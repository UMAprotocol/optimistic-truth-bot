import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "LAK": "p1",  # Los Angeles Kings
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
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {e}")
        return None
    return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # No game data found

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        if winner == "EDM":
            return "recommendation: p2"  # Oilers win
        elif winner == "LAK":
            return "recommendation: p1"  # Kings win
    elif game['Status'] == "Canceled":
        return "recommendation: p3"  # Game canceled, resolve 50-50
    elif game['Status'] == "Postponed":
        return "recommendation: p4"  # Game postponed, too early to resolve

    return "recommendation: p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to fetch NHL game data and determine the market resolution.
    """
    game_date = "2025-04-21"
    team1 = "EDM"
    team2 = "LAK"
    game = fetch_nhl_game_data(game_date, team1, team2)
    result = resolve_market(game)
    print(result)

if __name__ == "__main__":
    main()