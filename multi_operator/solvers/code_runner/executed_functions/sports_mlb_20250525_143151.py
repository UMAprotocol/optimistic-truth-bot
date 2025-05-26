import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-05-24"
TEAM1 = "SF"  # San Francisco Giants
TEAM2 = "WAS"  # Washington Nationals

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and analyze the game
def analyze_game():
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{GAME_DATE}")
    if not games:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{GAME_DATE}")
    
    if games:
        for game in games:
            if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or \
               game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return "Giants" if game['HomeTeam'] == TEAM1 else "Nationals"
                    else:
                        return "Nationals" if game['HomeTeam'] == TEAM2 else "Giants"
                elif game['Status'] == "Canceled":
                    return "50-50"
                elif game['Status'] == "Postponed":
                    return "Postponed"
    return "Too early to resolve"

# Main execution
result = analyze_game()
if result == "Giants":
    print("recommendation: p2")
elif result == "Nationals":
    print("recommendation: p1")
elif result == "50-50":
    print("recommendation: p3")
elif result == "Postponed":
    print("recommendation: p4")
else:
    print("recommendation: p4")