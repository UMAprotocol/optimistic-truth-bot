import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MEM": "p2",  # Memphis Grizzlies
    "OKC": "p1",  # Oklahoma City Thunder
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

def fetch_nba_game_data(game_date, team1, team2):
    """
    Fetches NBA game data for the specified teams on the given date.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={NBA_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching NBA game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # Too early to resolve or no data available

    if game['Status'] == "Canceled":
        return "p3"  # Game canceled, resolve as 50-50
    elif game['Status'] == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamScore']
        away_score = game['AwayTeamScore']

        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        return RESOLUTION_MAP.get(winner, "p4")
    else:
        return "p4"  # Game not completed or postponed

def main():
    """
    Main function to determine the outcome of the NBA game between Grizzlies and Thunder.
    """
    game_date = "2025-04-22"
    team1 = "MEM"  # Memphis Grizzlies
    team2 = "OKC"  # Oklahoma City Thunder

    game_data = fetch_nba_game_data(game_date, team1, team2)
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()