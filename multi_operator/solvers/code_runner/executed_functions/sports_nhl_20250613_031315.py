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

# Constants for the NHL game
GAME_DATE = "2025-06-12"
TEAM1 = "FLA"  # Florida Panthers
TEAM2 = "EDM"  # Edmonton Oilers

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

def get_game_data(date):
    """Fetch game data for the specified date."""
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def analyze_game(games):
    """Analyze game data to determine if the game went to overtime."""
    for game in games:
        if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
            if game['Status'] == "Final":
                if game['IsOvertime']:
                    return "Yes"
                else:
                    return "No"
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "50-50"
    return None

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game(games)
        if result:
            print("recommendation:", RESOLUTION_MAP[result])
        else:
            print("recommendation: p3")  # Default to 50-50 if no specific game data found
    else:
        print("recommendation: p3")  # Default to 50-50 if API call fails