import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "WSH": "p2",  # Washington Capitals
    "PIT": "p1",  # Pittsburgh Penguins
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nhl/GamesByDate/{game_date}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logging.error(f"Failed to fetch NHL game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'WSH' and game['AwayTeam'] == 'PIT' or game['HomeTeam'] == 'PIT' and game['AwayTeam'] == 'WSH':
            if game['Status'] == 'Final':
                if game['HomeTeam'] == 'WSH' and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p2"  # Capitals win
                elif game['AwayTeam'] == 'PIT' and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p1"  # Penguins win
            elif game['Status'] == 'Canceled':
                return "recommendation: p3"  # Game canceled, resolve 50-50
            elif game['Status'] == 'Postponed':
                return "recommendation: p4"  # Game postponed, too early to resolve
    return "recommendation: p4"  # No matching game found or unresolved status

def main():
    """
    Main function to determine the outcome of the Capitals vs. Penguins game.
    """
    game_date = "2025-04-17"
    games = fetch_nhl_game_data(game_date)
    if games:
        result = resolve_market(games)
    else:
        result = "recommendation: p4"  # Unable to fetch data or no games on the specified date
    print(result)

if __name__ == "__main__":
    main()