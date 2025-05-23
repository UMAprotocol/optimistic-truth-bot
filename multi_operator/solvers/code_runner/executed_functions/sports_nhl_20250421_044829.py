import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIN": "p2",  # Minnesota Wild
    "VGK": "p1",  # Vegas Golden Knights
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
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nhl/GamesByDate/{game_date}?key={NHL_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logging.info("Proxy failed, falling back to primary endpoint")
        # Fallback to primary endpoint if proxy fails
        response = requests.get(primary_url, timeout=10)
        response.raise_for_status()

    return response.json()

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'MIN' or game['AwayTeam'] == 'MIN':
            if game['HomeTeam'] == 'VGK' or game['AwayTeam'] == 'VGK':
                if game['Status'] == "Final":
                    if game['HomeTeam'] == 'MIN' and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"  # Wild win
                    elif game['AwayTeam'] == 'MIN' and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p2"  # Wild win
                    elif game['HomeTeam'] == 'VGK' and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p1"  # Golden Knights win
                    elif game['AwayTeam'] == 'VGK' and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p1"  # Golden Knights win
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, too early to resolve
    return "recommendation: p4"  # No matching game found or other statuses

def main():
    """
    Main function to fetch NHL game data and determine the market resolution.
    """
    game_date = "2025-04-20"
    games = fetch_nhl_game_data(game_date)
    resolution = resolve_market(games)
    print(resolution)

if __name__ == "__main__":
    main()