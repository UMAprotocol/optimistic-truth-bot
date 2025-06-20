import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game result
def find_game_result():
    date_of_game = "2025-06-12"
    team1 = "The MongolZ"
    team2 = "Liquid"
    game_date_formatted = datetime.strptime(date_of_game, "%Y-%m-%d").strftime("%Y%m%d")

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{game_date_formatted}")
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{game_date_formatted}")

    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    if winner == team1:
                        return "p2"  # The MongolZ win
                    else:
                        return "p1"  # Liquid win
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p3"  # Game canceled or postponed
    return "p3"  # Default to 50-50 if no conclusive result

# Main execution
if __name__ == "__main__":
    result = find_game_result()
    print(f"recommendation: {result}")