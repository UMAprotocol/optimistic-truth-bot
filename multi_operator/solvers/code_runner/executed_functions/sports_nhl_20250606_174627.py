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

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "NRG": "p2",  # NRG qualifies for Stage 2
    "not_qualified": "p1",  # NRG does not qualify
    "unknown": "p3"  # Unknown or 50-50
}

# Function to get data from API
def get_data_from_api(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

# Function to check if NRG qualifies for Stage 2
def check_nrg_qualification():
    current_date = datetime.now()
    event_date = datetime(2025, 7, 28, 23, 59)  # Event date July 28, 2025 11:59 PM ET
    if current_date > event_date:
        url = f"{PRIMARY_ENDPOINT}/scores/json/TeamSeasonStats/2025"
        data = get_data_from_api(url)
        if data:
            for team_stats in data:
                if team_stats['Team'] == 'NRG' and team_stats['QualifiedForStage2']:
                    return RESOLUTION_MAP["NRG"]
            return RESOLUTION_MAP["not_qualified"]
        else:
            return RESOLUTION_MAP["unknown"]
    else:
        return RESOLUTION_MAP["unknown"]

# Main execution
if __name__ == "__main__":
    result = check_nrg_qualification()
    print(f"recommendation: {result}")