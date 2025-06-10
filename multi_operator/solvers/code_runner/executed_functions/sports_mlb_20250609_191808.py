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
GAME_DATE = "2025-06-01"
TEAM1 = "STL"  # St. Louis Cardinals
TEAM2 = "TEX"  # Texas Rangers

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
            if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return "recommendation: p2"  # Cardinals win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Rangers win
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, check later
    return "recommendation: p4"  # No data or game not found

# Main execution
if __name__ == "__main__":
    result = analyze_game()
    print(result)