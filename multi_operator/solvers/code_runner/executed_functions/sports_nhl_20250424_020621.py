import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIA": "p2",  # Miami Heat
    "CLE": "p1",  # Cleveland Cavaliers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data(date, team1, team2):
    """
    Fetches NBA game data for the specified date and teams.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.RequestException as e:
        logging.error(f"Error fetching NBA game data: {e}")
    return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # Too early to resolve or no data

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamScore']
        away_score = game['AwayTeamScore']
        
        if home_score > away_score:
            return RESOLUTION_MAP[home_team]
        else:
            return RESOLUTION_MAP[away_team]
    else:
        return "p4"  # Game not completed

def main():
    """
    Main function to determine the outcome of the NBA game between Miami Heat and Cleveland Cavaliers.
    """
    date = "2025-04-23"
    team1 = "MIA"
    team2 = "CLE"
    game = fetch_nba_game_data(date, team1, team2)
    resolution = resolve_market(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()