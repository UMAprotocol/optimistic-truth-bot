import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on conference
RESOLUTION_MAP = {
    "East": "p2",  # Eastern Conference
    "West": "p1"   # Western Conference
}

def get_winner():
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/scores/json/StanleyCupFinalWinner", headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}/scores/json/StanleyCupFinalWinner", headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['Conference']
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    winner_conference = get_winner()
    if winner_conference and winner_conference in RESOLUTION_MAP:
        recommendation = RESOLUTION_MAP[winner_conference]
    else:
        recommendation = "p3"  # Unknown or error case
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()