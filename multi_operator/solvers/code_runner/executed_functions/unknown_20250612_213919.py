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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, requests.Timeout):
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data: {str(e)}")
            return None

# Function to determine the outcome of the match
def resolve_match():
    date_str = "2025-06-12"
    team1 = "Spirit"
    team2 = "Lynn Vision"
    path = f"/scores/json/GamesByDate/{date_str}"

    games = make_request(PRIMARY_ENDPOINT, path)
    if games is None:
        return "recommendation: p3"  # Assume unknown/50-50 if data retrieval fails

    for game in games:
        if team1 in game['HomeTeamName'] and team2 in game['AwayTeamName']:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p2"  # Spirit wins
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return "recommendation: p1"  # Lynn Vision wins
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "recommendation: p3"  # Match canceled or postponed
            else:
                return "recommendation: p3"  # Match not final, assume 50-50

    return "recommendation: p3"  # No match found or no conclusive result

# Main execution
if __name__ == "__main__":
    result = resolve_match()
    print(result)