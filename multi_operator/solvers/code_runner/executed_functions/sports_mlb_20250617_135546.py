import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to make GET requests
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_match(date_str, player1, player2):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_str}"
    games = get_data(url)
    if games is None:
        return "p4"  # Unable to fetch data

    for game in games:
        teams = {game['HomeTeam'], game['AwayTeam']}
        if player1 in teams and player2 in teams:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                if winner == player1:
                    return "p1"
                elif winner == player2:
                    return "p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p3"
            else:
                return "p4"  # Game not completed
    return "p4"  # No matching game found

# Main execution function
def main():
    # Define the match details
    match_date = "2025-06-17"
    player1 = "Fonseca"  # Corresponds to p2
    player2 = "Cobolli"  # Corresponds to p1

    # Resolve the match
    result = resolve_match(match_date, player1, player2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()