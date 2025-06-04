import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API key for HLTV
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Event details
EVENT_DATE = "2025-06-03"
TEAM1 = "B8"
TEAM2 = "Imperial"
EVENT_ID = "7902"  # BLAST.tv Austin Major 2025

# HLTV API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the match result
def check_match_result(event_id, team1, team2, event_date):
    # Format date for API request
    formatted_date = datetime.strptime(event_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"

    # Make the request to the proxy endpoint
    result = make_request(url, HEADERS)
    if result is None:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
        result = make_request(url, HEADERS)

    # Analyze the result
    if result:
        for game in result:
            if game['EventId'] == event_id and {team1, team2} == {game['HomeTeam'], game['AwayTeam']}:
                if game['Status'] == "Final":
                    if game['Winner'] == team1:
                        return "p1"
                    elif game['Winner'] == team2:
                        return "p2"
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p3"
        return "p4"  # Game not found or not yet played
    return "p4"  # No data available

# Main execution
if __name__ == "__main__":
    recommendation = check_match_result(EVENT_ID, TEAM1, TEAM2, EVENT_DATE)
    print(f"recommendation: {recommendation}")