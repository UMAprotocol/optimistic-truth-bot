import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

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

    # Convert ET to UTC for API compatibility
    et = pytz.timezone('US/Eastern')
    utc = pytz.utc
    game_date = datetime.strptime(date + " 10:00", "%Y-%m-%d %H:%M")
    game_date = et.localize(game_date).astimezone(utc).strftime('%Y-%m-%dT%H:%MZ')

    url = f"https://api.sportsdata.io/v3/cricket/scores/json/MatchesByDate/{game_date}?key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == "Royal Challengers Bangalore" and game['AwayTeamName'] == "Delhi Capitals":
                return game
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary

    Returns:
        Resolution string (p1, p2, p3)
    """
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    status = game.get("Status")
    if status == "Final":
        home_score = game.get("HomeScore")
        away_score = game.get("AwayScore")
        if home_score > away_score:
            return "recommendation: " + RESOLUTION_MAP["Bangalore"]
        else:
            return "recommendation: " + RESOLUTION_MAP["Delhi"]
    else:
        # Check if the current time is past the game day
        current_time = datetime.utcnow()
        game_end_time = datetime(2025, 4, 11, 3, 59, 59)  # 11:59 PM ET in UTC
        if current_time > game_end_time:
            return "recommendation: " + RESOLUTION_MAP["50-50"]
        else:
            return "recommendation: " + RESOLUTION_MAP["50-50"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(resolution)

if __name__ == "__main__":
    main()