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

# Resolution conditions
RESOLUTION_MAP = {
    "NRG": "p2",  # NRG qualifies for Stage 2
    "no_qualification": "p1",  # NRG does not qualify
    "unknown": "p3",  # Unknown or 50-50
}

# Function to get data from API
def get_data_from_api(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check NRG qualification
def check_nrg_qualification():
    event_url = f"{PRIMARY_ENDPOINT}/scores/json/TeamSeasonStats/2025"
    data = get_data_from_api(event_url)
    if data is None:
        print("Failed to retrieve data.")
        return "p3"  # Unknown or 50-50 due to data retrieval failure

    # Check if NRG qualified for Stage 2
    for team_data in data:
        if team_data['Team'] == 'NRG' and team_data['QualifiedForStage2']:
            return RESOLUTION_MAP['NRG']
    
    return RESOLUTION_MAP['no_qualification']

# Main execution
if __name__ == "__main__":
    result = check_nrg_qualification()
    print(f"recommendation: {result}")