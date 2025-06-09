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
GAME_DATE = "2025-06-07"
HOME_TEAM = "Tigers"
AWAY_TEAM = "Cubs"

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/GamesByDate/"

# Function to make API requests
def make_api_request(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}{formatted_date}"
    proxy_url = f"{PROXY_ENDPOINT}{formatted_date}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None

# Function to determine the game outcome
def determine_outcome(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: p1"  # Home team wins
                elif away_score > home_score:
                    return "recommendation: p2"  # Away team wins
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled
            elif game['Status'] == "Postponed":
                return "recommendation: p4"  # Game postponed
    return "recommendation: p4"  # No game found or in progress

# Main function to run the program
def main():
    games = make_api_request(GAME_DATE)
    if games:
        result = determine_outcome(games, HOME_TEAM, AWAY_TEAM)
        print(result)
    else:
        print("No data available.")

if __name__ == "__main__":
    main()