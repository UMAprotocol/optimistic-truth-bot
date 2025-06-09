import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}
HLTV_URL = "https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate"
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game result
def find_game_result(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(f"{HLTV_URL}/{formatted_date}")
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "p2" if game['HomeTeam'] == team1 else "p1"
                    elif game['HomeTeamScore'] < game['AwayTeamScore']:
                        return "p1" if game['HomeTeam'] == team2 else "p2"
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p3"
    return "p3"

# Main function to run the market resolver
def main():
    date = "2025-06-07"
    team1 = "3DMAX"
    team2 = "BetBoom"
    result = find_game_result(date, team1, team2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()