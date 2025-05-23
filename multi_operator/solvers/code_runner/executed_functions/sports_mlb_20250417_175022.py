import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Mumbai Indians": "p2",
    "Sunrisers Hyderabad": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_ipl_game_data():
    """
    Fetches IPL game data for Mumbai Indians vs. Sunrisers Hyderabad on the specified date.
    """
    date = "2025-04-17"
    team1 = "Mumbai Indians"
    team2 = "Sunrisers Hyderabad"
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == team1 and game['AwayTeamName'] == team2:
                return game
            elif game['HomeTeamName'] == team2 and game['AwayTeamName'] == team1:
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # Too early to resolve

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open
    elif game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeamName']]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeamName']]
        else:
            return RESOLUTION_MAP["50-50"]
    else:
        return "p4"  # Too early to resolve

def main():
    """
    Main function to fetch IPL game data and determine the market resolution.
    """
    game_data = fetch_ipl_game_data()
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()