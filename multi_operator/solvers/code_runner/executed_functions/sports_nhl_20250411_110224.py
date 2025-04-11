import os
import requests
from dotenv import load_dotenv
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NHL_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Golden Knights": "p1",
    "Kraken": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

logger = logging.getLogger(__name__)

def fetch_game_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == "Final":
        home_score = game['HomeTeamScore']
        away_score = game['AwayTeamScore']
        if home_score > away_score:
            winning_team = game['HomeTeam']
        else:
            winning_team = game['AwayTeam']

        if winning_team == "VGK":
            return RESOLUTION_MAP["Golden Knights"]
        elif winning_team == "SEA":
            return RESOLUTION_MAP["Kraken"]
    elif game['Status'] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-10"
    team1 = "VGK"
    team2 = "SEA"

    game = fetch_game_data(date, team1, team2)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()