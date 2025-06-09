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
    "Astros": "p2",
    "Pirates": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {str(e)}")
        return None

def resolve_game_status(game):
    if game['Status'] == 'Final':
        if game['AwayTeam'] == 'HOU' and game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP["Astros"]
        elif game['HomeTeam'] == 'PIT' and game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP["Pirates"]
    elif game['Status'] == 'Canceled':
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function
def main():
    date_of_game = "2025-06-05"
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_of_game}"
    games_data = get_data(games_url, {"Ocp-Apim-Subscription-Key": MLB_API_KEY})

    if not games_data:
        # Try proxy if primary fails
        games_data = get_data(PROXY_ENDPOINT + f"/GamesByDate/{date_of_game}", {"Ocp-Apim-Subscription-Key": MLB_API_KEY})
        if not games_data:
            print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
            return

    for game in games_data:
        if game['AwayTeam'] == 'HOU' and game['HomeTeam'] == 'PIT':
            recommendation = resolve_game_status(game)
            print("recommendation:", recommendation)
            return

    print("recommendation:", RESOLUTION_MAP["Too early to resolve"])

if __name__ == "__main__":
    main()