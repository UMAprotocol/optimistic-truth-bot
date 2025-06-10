import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the game result
def check_game_result():
    # Define the date of the game and the teams involved
    game_date = "2025-05-31"
    team1 = "Paris Saint-Germain"
    team2 = "Inter Milan"

    # Attempt to use the proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{game_date}")
    if not games:
        # Fallback to the primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{game_date}")

    if games:
        for game in games:
            if team1 in game['HomeTeam'] and team2 in game['AwayTeam']:
                home_goals = game['HomeTeamGoals']
                away_goals = game['AwayTeamGoals']
                if home_goals > away_goals:
                    return "p1"  # Home team wins
                elif away_goals > home_goals:
                    return "p2"  # Away team wins
                else:
                    return "p3"  # Draw or undetermined
    return "p4"  # No data available or game not found

# Main execution
if __name__ == "__main__":
    result = check_game_result()
    print(f"recommendation: {result}")