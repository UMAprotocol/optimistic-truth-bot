import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "NJD": "p2",  # New Jersey Devils
    "CAR": "p1",  # Carolina Hurricanes
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

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logger.error(f"Error fetching NHL game data: {e}")
        return None

def resolve_market(games, home_team, away_team):
    """
    Resolves the market based on the game data.
    """
    if not games:
        return "recommendation: p4"

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return f"recommendation: {RESOLUTION_MAP[home_team]}"
                elif away_score > home_score:
                    return f"recommendation: {RESOLUTION_MAP[away_team]}"
            elif game['Status'] == "Canceled":
                return "recommendation: p3"
            elif game['Status'] == "Postponed":
                return "recommendation: p4"
            else:
                return "recommendation: p4"

    return "recommendation: p4"

def main():
    game_date = "2025-04-22"
    home_team = "CAR"  # Carolina Hurricanes
    away_team = "NJD"  # New Jersey Devils

    games = fetch_nhl_game_data(game_date)
    result = resolve_market(games, home_team, away_team)
    print(result)

if __name__ == "__main__":
    main()