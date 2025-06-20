import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-06-13"
HOME_TEAM = "Mets"
AWAY_TEAM = "Rays"

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/GamesByDate/"

# Function to make API requests
def make_api_request(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}{formatted_date}"
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "p1"  # Home team wins
                elif away_score > home_score:
                    return "p2"  # Away team wins
            elif game['Status'] == "Canceled":
                return "p3"  # Game canceled
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled within the season
                rescheduled_games = make_api_request(GAME_DATE[:4] + "-12-31")
                if determine_outcome(rescheduled_games) is not None:
                    return determine_outcome(rescheduled_games)
                return "p3"  # Game postponed and not yet played
    return "p3"  # No game found or undetermined outcome

# Main execution
if __name__ == "__main__":
    games_on_date = make_api_request(GAME_DATE)
    if games_on_date:
        result = determine_outcome(games_on_date)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p3")  # Unable to retrieve data or no games on that date