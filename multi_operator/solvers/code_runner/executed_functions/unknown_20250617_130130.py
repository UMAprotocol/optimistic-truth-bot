import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HSBC_CHAMPIONSHIPS_URL = "https://www.lta.org.uk/fan-zone/international/hsbc-championships/"
PROXY_URL = "https://api.proxy.example.com/hsbc-championships/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
TIMEOUT = 10

# Helper functions
def get_match_result(url, player1, player2):
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        for match in data.get('matches', []):
            if match['player1'] == player1 and match['player2'] == player2:
                return match['result']
        return None
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {str(e)}")
        return None

def resolve_market(player1, player2):
    # Try proxy endpoint first
    result = get_match_result(PROXY_URL, player1, player2)
    if result is None:
        # Fallback to primary endpoint
        result = get_match_result(HSBC_CHAMPIONSHIPS_URL, player1, player2)
    
    if result is None:
        return "p3"  # Unknown or 50-50 if no data could be retrieved
    elif result == player1:
        return "p1"  # Fokina wins
    elif result == player2:
        return "p2"  # Alcaraz wins
    else:
        return "p3"  # Tie, canceled, or delayed

# Main execution
if __name__ == "__main__":
    player1 = "Alejandro Davidovich Fokina"
    player2 = "Carlos Alcaraz"
    recommendation = resolve_market(player1, player2)
    print(f"recommendation: {recommendation}")