import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Leon Draisaitl"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

def get_games_by_date(date):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from proxy endpoint: {e}")
            return None

def check_player_goals(games, player_name):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
            if game["Status"] == "Final":
                for player in game["PlayerStats"]:
                    if player["Name"] == player_name and player["Goals"] > 0.5:
                        return "Yes"
                return "No"
            else:
                return "50-50"
    return "50-50"

def main():
    today = datetime.utcnow().date()
    game_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").date()
    if game_date > today:
        logger.info("Game date is in the future.")
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    games = get_games_by_date(GAME_DATE)
    if not games:
        logger.info("No games data available.")
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    result = check_player_goals(games, PLAYER_NAME)
    print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()