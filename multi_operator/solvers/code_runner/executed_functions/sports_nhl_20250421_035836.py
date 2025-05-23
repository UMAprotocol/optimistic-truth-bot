import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "GSW": "p2",  # Golden State Warriors
    "HOU": "p1",  # Houston Rockets
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

def fetch_nba_game_data(game_date, home_team, away_team):
    """
    Fetches NBA game data for the specified date and teams.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={NBA_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching NBA game data: {e}")
        return None

def resolve_market(game_data):
    """
    Resolves the market based on the game data.
    """
    if not game_data:
        return "recommendation: p4"  # Too early to resolve or no data

    if game_data['Status'] == "Canceled":
        return "recommendation: p3"  # 50-50
    elif game_data['Status'] == "Final":
        home_score = game_data['HomeTeamScore']
        away_score = game_data['AwayTeamScore']
        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[game_data['HomeTeam']]}"
        else:
            return f"recommendation: {RESOLUTION_MAP[game_data['AwayTeam']]}"
    else:
        return "recommendation: p4"  # Game not completed

def main():
    """
    Main function to determine the outcome of the NBA game between Warriors and Rockets.
    """
    game_date = "2025-04-20"
    home_team = "GSW"  # Golden State Warriors abbreviation
    away_team = "HOU"  # Houston Rockets abbreviation

    game_data = fetch_nba_game_data(game_date, home_team, away_team)
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()