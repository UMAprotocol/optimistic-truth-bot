import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"
GAME_DATE = "2025-04-22"
BUCKS_ABBR = "MIL"
PACERS_ABBR = "IND"

# Resolution mapping
RESOLUTION_MAP = {
    BUCKS_ABBR: "p2",  # Bucks win
    PACERS_ABBR: "p1",  # Pacers win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or other outcomes
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data(api_key):
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        logging.warning("Proxy failed, trying primary endpoint")
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == BUCKS_ABBR and game['AwayTeam'] == PACERS_ABBR or \
           game['HomeTeam'] == PACERS_ABBR and game['AwayTeam'] == BUCKS_ABBR:
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "Unknown")
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return "Unknown"

def main():
    if not NBA_API_KEY:
        logging.error("NBA API key is not set. Please check your .env file.")
        return
    games = fetch_game_data(NBA_API_KEY)
    if games is None:
        logging.error("No game data available.")
        print("recommendation: p4")
        return
    resolution = resolve_market(games)
    print(f"recommendation: {RESOLUTION_MAP.get(resolution, 'p4')}")

if __name__ == "__main__":
    main()