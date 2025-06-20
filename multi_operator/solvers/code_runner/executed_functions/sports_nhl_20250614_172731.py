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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on team abbreviations
RESOLUTION_MAP = {
    "3DMAX": "p2",  # 3DMAX wins
    "paiN": "p1",   # paiN wins
    "50-50": "p3",  # Tie, canceled, or delayed
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game result
def find_game_result(event_id):
    # Try proxy endpoint first
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{event_id}"
    result = make_request(url, HEADERS)
    if result is None:
        # Fallback to primary endpoint
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{event_id}"
        result = make_request(url, HEADERS)
    
    if result:
        for game in result:
            if game['Status'] == 'Final':
                home_team = game['HomeTeam']
                away_team = game['AwayTeam']
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] in ['Canceled', 'Postponed']:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["50-50"]

# Main execution function
def main():
    event_id = "7902"  # Specific event ID for BLAST.tv Austin Major
    recommendation = find_game_result(event_id)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()