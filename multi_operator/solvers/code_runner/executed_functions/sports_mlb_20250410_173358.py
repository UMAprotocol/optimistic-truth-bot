import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Bangalore": "p2",  # Royal Challengers Bangalore win maps to p2
    "Delhi": "p1",      # Delhi Capitals win maps to p1
    "50-50": "p3",      # Game not completed maps to p3
}

def fetch_game_data():
    """
    Fetches game data for the IPL game between Royal Challengers Bangalore and Delhi Capitals.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-10"
    home_team = "RCB"  # Example abbreviation for Royal Challengers Bangalore
    away_team = "DC"   # Example abbreviation for Delhi Capitals

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/MatchesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            if (
                game_data.get("HomeTeamName") == "Royal Challengers Bangalore"
                and game_data.get("AwayTeamName") == "Delhi Capitals"
            ):
                return game_data

        return None

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the API

    Returns:
        Resolution string (p1, p2, p3)
    """
    if not game:
        return RESOLUTION_MAP["50-50"]

    status = game.get("Status")
    home_score = game.get("HomeScore")
    away_score = game.get("AwayScore")

    if status == "Final":
        if home_score > away_score:
            return RESOLUTION_MAP["Bangalore"]
        elif away_score > home_score:
            return RESOLUTION_MAP["Delhi"]
    else:
        current_time = datetime.utcnow()
        deadline = datetime(2025, 4, 11, 3, 59, 59)  # April 10, 11:59 PM ET in UTC
        if current_time > deadline:
            return RESOLUTION_MAP["50-50"]
        else:
            return "Too early to resolve"

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()