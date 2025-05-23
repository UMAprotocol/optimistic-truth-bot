import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "DET": "p2",  # Detroit Red Wings
    "TOR": "p1",  # Toronto Maple Leafs
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data(game_date, team1, team2):
    """
    Fetches NHL game data for the specified date and teams.
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
        logging.error(f"Failed to fetch game data: {e}")
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
        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game['Status'] == "Canceled":
        return "recommendation: p3"
    elif game['Status'] == "Postponed":
        return "recommendation: p4"
    else:
        return "recommendation: p4"

def main():
    game_date = "2025-04-17"
    team1 = "DET"  # Detroit Red Wings
    team2 = "TOR"  # Toronto Maple Leafs

    game = fetch_nhl_game_data(game_date, team1, team2)
    result = resolve_market(game)
    print(result)

if __name__ == "__main__":
    main()