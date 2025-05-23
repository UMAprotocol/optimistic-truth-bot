import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "FLA": "p2",  # Florida Panthers
    "TBL": "p1",  # Tampa Bay Lightning
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data(game_date, team1, team2):
    """
    Fetches NHL game data for the specified teams and date.
    """
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nhl/GamesByDate/{game_date}?key={NHL_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Search for the specific game
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # No game data found

    if game['Status'] == "Canceled":
        return "recommendation: p3"  # Game canceled, resolve as 50-50
    elif game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "FLA":
            return "recommendation: p2"  # Panthers win
        elif winner == "TBL":
            return "recommendation: p1"  # Lightning win
    else:
        return "recommendation: p4"  # Game not completed or postponed

def main():
    game_date = "2025-04-22"
    team1 = "FLA"  # Florida Panthers
    team2 = "TBL"  # Tampa Bay Lightning

    game_data = fetch_nhl_game_data(game_date, team1, team2)
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()