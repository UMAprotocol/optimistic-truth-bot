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

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check if Nemiga qualified for Stage 2
def check_nemiga_qualification():
    event_id = "7902"  # BLAST.tv Austin Major 2025 event ID from HLTV
    url = f"/scores/json/Standings/{event_id}"
    data = make_request(url)
    if data:
        for team in data:
            if team['Team'] == 'Nemiga' and team['QualifiedForNextStage']:
                return "p2"  # Yes, Nemiga qualified
        return "p1"  # No, Nemiga did not qualify
    return "p3"  # Unknown or data not available

# Main execution
if __name__ == "__main__":
    result = check_nemiga_qualification()
    print(f"recommendation: {result}")