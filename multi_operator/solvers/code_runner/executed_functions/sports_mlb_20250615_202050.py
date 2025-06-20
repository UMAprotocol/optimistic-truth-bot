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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # Fallback to proxy if primary fails
        try:
            proxy_url = PROXY_ENDPOINT + url.split(PRIMARY_ENDPOINT)[-1]
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data from both primary and proxy endpoints: {e}")
            return None

# Function to determine the outcome of the game
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(games_today_url)

    if games is None:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']

                if winner == team1:
                    return "recommendation: p1"
                elif winner == team2:
                    return "recommendation: p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "recommendation: p3"
            else:
                return "recommendation: p4"

    return "recommendation: p4"  # No matching game found or game not yet started

# Main execution
if __name__ == "__main__":
    # Game details
    game_date = "2025-06-15"
    team1 = "ATL"  # Atlanta Braves
    team2 = "COL"  # Colorado Rockies

    result = resolve_game(game_date, team1, team2)
    print(result)