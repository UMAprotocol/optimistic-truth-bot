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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print(f"Falling back to primary endpoint due to error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error accessing API: {e}")
            return None

# Function to find the game and determine the outcome
def resolve_game(date, team1, team2):
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    if games_today is None:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p2" if game['HomeTeam'] == team1 else "p1"
                else:
                    return "p1" if game['AwayTeam'] == team1 else "p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p3"
            else:
                return "p4"  # Game not final
    return "p4"  # No matching game found

# Main execution function
if __name__ == "__main__":
    # Extracting the specific game date and teams from the question
    game_date = "2025-05-23"
    team1 = "Royal Challengers Bangalore"
    team2 = "Sunrisers Hyderabad"

    # Convert game date to the required format
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Resolve the game and print the recommendation
    recommendation = resolve_game(formatted_date, team1, team2)
    print(f"recommendation: {recommendation}")