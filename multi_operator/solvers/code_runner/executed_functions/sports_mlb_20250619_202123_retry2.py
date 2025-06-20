import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Pirates": "p2",  # Pittsburgh Pirates win
    "Tigers": "p1",   # Detroit Tigers win
    "Canceled": "p3", # Game canceled
    "Postponed": "p4" # Game postponed or in progress
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # Fallback to proxy if primary fails
        try:
            proxy_url = PROXY_ENDPOINT + url[len(PRIMARY_ENDPOINT):]
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error accessing API through primary and proxy endpoints: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return RESOLUTION_MAP[home_team]
                    else:
                        return RESOLUTION_MAP[away_team]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["Canceled"]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Postponed"]
    return "p4"  # Default to unresolved if no data or game not found

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-19"
    home_team = "Tigers"  # Detroit Tigers
    away_team = "Pirates" # Pittsburgh Pirates
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")