import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-06-15"
TEAM1 = "TEX"  # Texas Rangers
TEAM2 = "CWS"  # Chicago White Sox

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/GamesByDate/"

# Function to make API requests
def make_api_request(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            # If proxy fails, fallback to primary endpoint
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None

# Function to determine the game outcome
def determine_outcome(games):
    for game in games:
        if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or \
           game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "p1" if game['HomeTeam'] == TEAM1 else "p2"
                else:
                    return "p2" if game['HomeTeam'] == TEAM1 else "p1"
            elif game['Status'] == "Canceled":
                return "p3"
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled within the same day
                new_date = datetime.strptime(GAME_DATE, "%Y-%m-%d") + datetime.timedelta(days=1)
                new_date_str = new_date.strftime("%Y-%m-%d")
                new_games = make_api_request(new_date_str)
                return determine_outcome(new_games)
    return "p4"  # If no game found or game is not yet completed

# Main execution
if __name__ == "__main__":
    games_today = make_api_request(GAME_DATE)
    if games_today:
        result = determine_outcome(games_today)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")