import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, team1, team2):
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    if not games_today:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p1" if game['HomeTeam'] == team1 else "p2"
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return "p1" if game['AwayTeam'] == team1 else "p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p3"
            return "p4"  # Game not completed yet
    return "p4"  # No matching game found

# Main execution function
def main():
    # Define the game date and teams involved
    game_date = "2025-05-10"
    team1 = "Kolkata Knight Riders"
    team2 = "Sunrisers Hyderabad"

    # Convert game date to the required format
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Determine the outcome
    outcome = find_game_and_determine_outcome(formatted_date, team1, team2)
    print(f"recommendation: {outcome}")

if __name__ == "__main__":
    main()