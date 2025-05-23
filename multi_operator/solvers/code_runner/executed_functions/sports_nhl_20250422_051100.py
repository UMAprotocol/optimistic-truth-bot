import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "COL": "p2",  # Colorado Avalanche
    "DAL": "p1",  # Dallas Stars
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy/GamesByDate/"

def fetch_game_data(date):
    headers = {'Ocp-Apim-Subscription-Key': NHL_API_KEY}
    url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        logging.warning("Proxy failed, trying primary endpoint")
        url = f"{PRIMARY_ENDPOINT}{date}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == 'COL' and game['AwayTeam'] == 'DAL' or game['HomeTeam'] == 'DAL' and game['AwayTeam'] == 'COL':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return f"recommendation: {RESOLUTION_MAP[winner]}"
            elif game['Status'] == 'Canceled':
                return f"recommendation: {RESOLUTION_MAP['50-50']}"
            elif game['Status'] == 'Postponed':
                return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"
    return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"

def main():
    game_date = "2025-04-21"
    games = fetch_game_data(game_date)
    if games:
        result = resolve_market(games)
    else:
        result = f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"
    print(result)

if __name__ == "__main__":
    main()