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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/scores/json"

# Function to make API requests
def make_api_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    games = make_api_request(PRIMARY_ENDPOINT, f"GamesByDate/{game_date}")
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return "p2"  # Home team wins
                    elif away_score > home_score:
                        return "p1"  # Away team wins
                elif game['Status'] == 'Canceled':
                    return "p3"  # Game canceled
                elif game['Status'] == 'Postponed':
                    # Check for rescheduled game
                    return "p4"  # Game postponed, check later
    return "p4"  # Default case if no data found or game not completed

# Main execution function
def main():
    game_date = "2025-05-31"
    home_team = "TEX"  # Texas Rangers
    away_team = "STL"  # St. Louis Cardinals
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()