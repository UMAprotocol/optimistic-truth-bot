import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Key for HLTV
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Event details
EVENT_DATE = "2025-06-15"
TEAM1 = "Virtus.pro"
TEAM2 = "paiN"
EVENT_ID = "7902"

# HLTV API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the match result
def check_match_result():
    # Try proxy endpoint first
    games = make_request(f"{PROXY_ENDPOINT}/{EVENT_DATE}")
    if not games:
        # Fallback to primary endpoint
        games = make_request(f"{PRIMARY_ENDPOINT}/{EVENT_DATE}")

    if games:
        for game in games:
            if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2:
                if game['Status'] == "Final":
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p1"  # Virtus.pro wins
                    elif game['HomeTeamScore'] < game['AwayTeamScore']:
                        return "recommendation: p2"  # paiN wins
                    else:
                        return "recommendation: p3"  # Tie
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"  # 50-50
    return "recommendation: p3"  # Default to 50-50 if no conclusive result

# Main function to run the program
if __name__ == "__main__":
    result = check_match_result()
    print(result)