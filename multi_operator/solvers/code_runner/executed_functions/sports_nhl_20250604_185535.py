import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Constants for the specific market
MATCH_DATE = "2025-05-31"
TEAM1 = "PSG"  # Paris Saint-Germain
TEAM2 = "INT"  # Inter Milan
PLAYER_NAME = "Denzel Dumfries"

# Resolution conditions
RESOLUTION_MAP = {
    "YES": "p2",
    "NO": "p1",
    "UNKNOWN": "p3"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(data, player_name):
    if data:
        for player in data.get('PlayerStats', []):
            if player.get('Name') == player_name and player.get('Goals', 0) > 0:
                return True
    return False

def resolve_market():
    # Construct URL for the match data
    match_date_formatted = datetime.strptime(MATCH_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{match_date_formatted}"

    # Fetch data from proxy endpoint
    data = get_data(url, HEADERS)
    if not data:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{match_date_formatted}"
        data = get_data(url, HEADERS)

    # Check if the match and player data are available
    if data:
        for game in data:
            if {game.get('HomeTeam'), game.get('AwayTeam')} == {TEAM1, TEAM2}:
                if game.get('Status') == 'Final':
                    if check_player_goals(game, PLAYER_NAME):
                        return RESOLUTION_MAP["YES"]
                    else:
                        return RESOLUTION_MAP["NO"]
                else:
                    return RESOLUTION_MAP["UNKNOWN"]
    return RESOLUTION_MAP["UNKNOWN"]

# Run the market resolution
recommendation = resolve_market()
print(f"recommendation: {recommendation}")