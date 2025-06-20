import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Constants for the event
EVENT_DATE = "2025-06-17"
PLAYER1 = "Carlos Alcaraz"
PLAYER2 = "Alejandro Davidovich Fokina"
TOURNAMENT = "HSBC Championships"

# Resolution map
RESOLUTION_MAP = {
    "Alcaraz": "p2",
    "Fokina": "p1",
    "50-50": "p3"
}

def get_match_data():
    # Construct the URL for the match data
    date_str = datetime.strptime(EVENT_DATE, "%Y-%m-%d").strftime("%Y%m%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_str}"

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
        if not response.ok:
            # If proxy fails, fallback to the primary endpoint
            response = requests.get(url, headers=HEADERS, timeout=10)
        if response.ok:
            return response.json()
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return None

def analyze_match_data(matches):
    for match in matches:
        if (PLAYER1 in match['Players'] and PLAYER2 in match['Players'] and
            TOURNAMENT in match['Tournament']):
            if match['Status'] == "Finished":
                winner = match['Winner']
                if winner == PLAYER1:
                    return RESOLUTION_MAP["Alcaraz"]
                elif winner == PLAYER2:
                    return RESOLUTION_MAP["Fokina"]
            elif match['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
    return "p3"  # Default to 50-50 if no match found or in progress

def main():
    matches = get_match_data()
    if matches:
        recommendation = analyze_match_data(matches)
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p3")  # Default to 50-50 if data retrieval fails

if __name__ == "__main__":
    main()