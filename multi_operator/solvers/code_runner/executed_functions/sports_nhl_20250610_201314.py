import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
RESOLUTION_MAP = {
    "B8": "p2",  # B8 wins
    "LV": "p1",  # Lynn Vision wins
    "50-50": "p3"
}

# Helper functions
def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {str(e)}")
        return None

def resolve_match(data, team1, team2):
    if not data:
        return "p3"  # Assume 50-50 if no data could be retrieved
    for match in data:
        if match['HomeTeam'] == team1 and match['AwayTeam'] == team2:
            if match['Status'] == "Final":
                home_score = match['HomeTeamRuns']
                away_score = match['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[team1]
                elif away_score > home_score:
                    return RESOLUTION_MAP[team2]
            elif match['Status'] in ["Canceled", "Postponed"]:
                return "p3"
    return "p4"  # Match not found or not yet played

# Main execution
def main():
    date_of_match = "2025-06-10"
    team1 = "B8"
    team2 = "LV"

    # Try proxy endpoint first
    proxy_url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_of_match}"
    data = get_data(proxy_url, HEADERS)
    if not data:  # Fallback to primary endpoint if proxy fails
        primary_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_of_match}"
        data = get_data(primary_url, HEADERS)

    recommendation = resolve_match(data, team1, team2)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()