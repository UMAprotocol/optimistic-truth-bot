import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        print(f"Error during requests to {endpoint}: {str(e)}")
        return None

# Function to determine the outcome of the game
def resolve_market(date_str):
    games_today = make_request(PRIMARY_ENDPOINT, f"scores/json/GamesByDate/{date_str}")
    if not games_today:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if game['HomeTeam'] == 'NYK' and game['AwayTeam'] == 'IND':
            if game['Status'] == 'Final':
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p2"  # Knicks win
                else:
                    return "p1"  # Pacers win
            elif game['Status'] == 'Postponed':
                return "p4"  # Market remains open
            elif game['Status'] == 'Canceled':
                return "p3"  # Market resolves 50-50
    return "p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-31"
    print("recommendation:", resolve_market(game_date))