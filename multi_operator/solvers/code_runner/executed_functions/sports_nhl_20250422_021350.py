import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MTL": "p2",  # Montreal Canadiens
    "WSH": "p1",  # Washington Capitals
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data(game_date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
    return None

def resolve_market(game):
    if not game:
        return "p4"  # No game data found or API request failed

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        return RESOLUTION_MAP.get(winner, "p3")
    elif game['Status'] == "Canceled":
        return "p3"
    elif game['Status'] == "Postponed":
        return "p4"
    else:
        return "p4"  # Game not completed or other statuses

def main():
    game_date = "2025-04-21"
    team1 = "MTL"  # Montreal Canadiens
    team2 = "WSH"  # Washington Capitals

    game = fetch_nhl_game_data(game_date, team1, team2)
    resolution = resolve_market(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()