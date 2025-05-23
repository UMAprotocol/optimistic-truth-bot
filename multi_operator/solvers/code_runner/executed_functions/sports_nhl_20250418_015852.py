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

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the Capitals vs Penguins game on the specified date.
    """
    date = "2025-04-17"
    team1 = "WSH"
    team2 = "PIT"
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={NHL_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "p2" if game['HomeTeam'] == team1 else "p1"
                    else:
                        return "p1" if game['HomeTeam'] == team2 else "p2"
                elif game['Status'] == "Postponed":
                    return "p4"  # Market remains open
                elif game['Status'] == "Canceled":
                    return "p3"  # Resolve 50-50
                else:
                    return "p4"  # Game not completed yet
        return "p4"  # No matching game found

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NHL game data: {e}")
        return "p4"  # Unable to resolve due to error

def main():
    resolution = fetch_nhl_game_data()
    print(f"recommendation: {RESOLUTION_MAP.get(resolution, 'p4')}")

if __name__ == "__main__":
    main()