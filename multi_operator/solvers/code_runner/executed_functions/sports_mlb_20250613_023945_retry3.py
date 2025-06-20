import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Yankees": "p2",
    "Royals": "p1",
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
    if response.ok:
        return response.json()
    response.raise_for_status()

def analyze_game_data(games):
    """ Analyze game data to determine the outcome """
    for game in games:
        if game['Day'] == '2025-06-12' and game['AwayTeam'] == 'NYY' and game['HomeTeam'] == 'KC':
            if game['Status'] == 'Final':
                if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP['Yankees']
                elif game['AwayTeamRuns'] < game['HomeTeamRuns']:
                    return RESOLUTION_MAP['Royals']
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP['Postponed']
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP['Canceled']
    return "p4"  # If no relevant game is found or it's still in progress

def main():
    date_str = '2025-06-12'
    games = get_game_data(date_str)
    result = analyze_game_data(games)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()