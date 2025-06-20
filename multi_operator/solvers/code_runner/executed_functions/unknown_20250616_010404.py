import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API key for HLTV, loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

# URL configurations
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Event details extracted from the question
EVENT_DATE = "2025-06-15"
TEAM1 = "Virtus.pro"
TEAM2 = "paiN"
MARKET_ID = "552628"

def get_match_result():
    # Construct the URL for the match data
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{EVENT_DATE}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{EVENT_DATE}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if not response.ok:
                response.raise_for_status()
        
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or \
               game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "p1" if game['HomeTeam'] == TEAM1 else "p2"
                    elif away_score > home_score:
                        return "p1" if game['AwayTeam'] == TEAM1 else "p2"
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p3"
        return "p3"  # Default to 50-50 if no conclusive result or game not found
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Default to 50-50 in case of network or API errors

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")