import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "STL": "p2",  # St. Louis Blues
    "WPG": "p1",  # Winnipeg Jets
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the St. Louis Blues vs. Winnipeg Jets game on the specified date.
    """
    date = "2025-04-21"
    team1 = "STL"
    team2 = "WPG"
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
                        return "p1" if game['HomeTeam'] == team1 else "p2"
                elif game['Status'] == "Canceled":
                    return "p3"
                elif game['Status'] == "Postponed":
                    return "p4"
        return "p4"  # If no specific game is found or it's still scheduled

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NHL game data: {e}")
        return "p4"

def main():
    """
    Main function to determine the outcome of the NHL game.
    """
    result = fetch_nhl_game_data()
    print(f"recommendation: {RESOLUTION_MAP.get(result, 'p4')}")

if __name__ == "__main__":
    main()