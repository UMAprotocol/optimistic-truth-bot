import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Dodgers": "p2",
    "Mets": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint if primary fails
            proxy_url = url.replace(PRIMARY_ENDPOINT, PROXY_ENDPOINT)
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data from both primary and proxy endpoints: {e}")
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
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return RESOLUTION_MAP[home_team]
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return RESOLUTION_MAP[away_team]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Postponed"]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["Canceled"]
    return RESOLUTION_MAP["Unknown"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-24"
    home_team = "Mets"
    away_team = "Dodgers"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")