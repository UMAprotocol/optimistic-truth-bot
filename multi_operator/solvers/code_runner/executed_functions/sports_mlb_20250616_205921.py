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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy/GamesByDate/"

# Function to make API requests
def make_request(date):
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    primary_url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(primary_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check if the game had 4+ goals
def check_goals(games, team1, team2):
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            total_goals = game['HomeTeamRuns'] + game['AwayTeamRuns']
            if total_goals > 3.5:
                return "p2"  # Yes, more than 3.5 goals
            else:
                return "p1"  # No, not more than 3.5 goals
    return "p3"  # Game not found or data insufficient

# Main function to resolve the market
def resolve_market():
    match_date = "2025-06-16"
    team1 = "Chelsea"
    team2 = "LAFC"
    games = make_request(match_date)
    if games:
        result = check_goals(games, team1, team2)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p3")  # Unknown or API failure

# Run the resolver
if __name__ == "__main__":
    resolve_market()