import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and date information
GAME_DATE = "2025-06-12"
TEAMS = ("FLA", "EDM")  # Florida Panthers and Edmonton Oilers

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Game decided in overtime
    "No": "p1",   # Game not decided in overtime
    "50-50": "p3" # Game canceled or postponed
}

def get_game_data(date, teams):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if game['Status'] == "Final":
        if game['IsOvertime']:
            return "recommendation: " + RESOLUTION_MAP["Yes"]
        else:
            return "recommendation: " + RESOLUTION_MAP["No"]
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, TEAMS)
    result = resolve_market(game_info)
    print(result)