import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "PHI": "p2",  # Philadelphia Flyers
    "BUF": "p1",  # Buffalo Sabres
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data(game_date, home_team, away_team):
    """
    Fetches NHL game data for a specific date and teams.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
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
        return "p4"  # No game data found

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['AwayTeamScore'] > game['HomeTeamScore']:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == "Canceled":
        return "p3"  # Game canceled, resolve as 50-50
    elif game['Status'] == "Postponed":
        return "p4"  # Game postponed, too early to resolve

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to determine the outcome of the NHL game between Flyers and Sabres.
    """
    game_date = "2025-04-17"
    home_team = "BUF"  # Buffalo Sabres
    away_team = "PHI"  # Philadelphia Flyers

    game_data = fetch_nhl_game_data(game_date, home_team, away_team)
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()