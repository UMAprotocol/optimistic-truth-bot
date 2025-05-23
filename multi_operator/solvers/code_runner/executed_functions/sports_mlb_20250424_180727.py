import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError("SPORTS_DATA_IO_MLB_API_KEY not found in environment variables.")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Royal Challengers Bangalore": "p2",
    "Rajasthan Royals": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified IPL game.
    
    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-24"
    team1 = "Royal Challengers Bangalore"
    team2 = "Rajasthan Royals"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
                return game
            elif game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game

        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return "p4"  # Too early to resolve

    status = game.get("Status")
    if status in ["Scheduled", "InProgress"]:
        return "p4"  # Too early to resolve
    elif status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP[game["HomeTeam"]]
        else:
            return RESOLUTION_MAP[game["AwayTeam"]]
    elif status == "Postponed":
        return "p4"  # Market remains open
    elif status == "Canceled":
        return "p3"  # Resolve 50-50

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to determine the resolution of the IPL game market.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()