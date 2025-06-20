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

# Resolution map based on the outcomes
RESOLUTION_MAP = {
    "Alcaraz": "p2",
    "Fokina": "p1",
    "50-50": "p3"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Main function to determine the outcome of the match
def resolve_match():
    date_str = "2025-06-17"
    match_info = "GamesByDate/2025-JUN-17"
    # Try proxy endpoint first
    data = make_request(PROXY_ENDPOINT, match_info)
    if not data:
        # Fallback to primary endpoint if proxy fails
        data = make_request(PRIMARY_ENDPOINT, match_info)
    
    if not data:
        return "recommendation: p4"  # Unable to fetch data

    # Search for the specific match
    for game in data:
        if game['AwayTeam'] == "Alcaraz" and game['HomeTeam'] == "Davidovich Fokina":
            if game['Status'] == "Final":
                if game['Winner'] == "Alcaraz":
                    return f"recommendation: {RESOLUTION_MAP['Alcaraz']}"
                elif game['Winner'] == "Davidovich Fokina":
                    return f"recommendation: {RESOLUTION_MAP['Fokina']}"
            elif game['Status'] in ["Canceled", "Postponed"]:
                return f"recommendation: {RESOLUTION_MAP['50-50']}"
            else:
                return "recommendation: p4"  # Match not completed yet
    return "recommendation: p4"  # Match not found or no conclusive data

# Execute the function and print the result
if __name__ == "__main__":
    print(resolve_match())