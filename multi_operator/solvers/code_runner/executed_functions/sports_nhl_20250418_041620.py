import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "CGY": "p2",  # Calgary Flames
    "LAK": "p1",  # Los Angeles Kings
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
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch NHL game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['AwayTeam'] == "CGY" and game['HomeTeam'] == "LAK" or game['AwayTeam'] == "LAK" and game['HomeTeam'] == "CGY":
            if game['Status'] == "Final":
                if game['AwayTeam'] == "CGY" and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p2"  # Flames win
                elif game['HomeTeam'] == "CGY" and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p2"  # Flames win
                elif game['AwayTeam'] == "LAK" and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p1"  # Kings win
                elif game['HomeTeam'] == "LAK" and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p1"  # Kings win
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled, resolve 50-50
            elif game['Status'] == "Postponed":
                return "recommendation: p4"  # Game postponed, too early to resolve
    return "recommendation: p4"  # No matching game found or game not yet played

def main():
    game_date = "2025-04-17"
    games = fetch_nhl_game_data(game_date)
    if games:
        result = resolve_market(games)
    else:
        result = "recommendation: p4"  # Unable to fetch data or no games on this date
    print(result)

if __name__ == "__main__":
    main()