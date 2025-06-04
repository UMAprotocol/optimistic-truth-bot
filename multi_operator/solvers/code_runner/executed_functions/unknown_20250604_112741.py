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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, date):
    try:
        response = requests.get(f"{endpoint}{date}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during request to {endpoint}: {str(e)}")
        return None

# Function to find the game and determine the outcome
def find_game_and_outcome(games, team1, team2):
    for game in games:
        if team1 in game['Teams'] and team2 in game['Teams']:
            if game['Status'] == 'Final':
                winner = game['Winner']
                if winner == team1:
                    return "p1"
                elif winner == team2:
                    return "p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p3"
    return "p4"

# Main function to process the event
def process_event(date, team1, team2):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, date)
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, date)
        if games is None:
            return "p4"  # Unable to get data from both endpoints

    # Determine the outcome based on the games data
    return find_game_and_outcome(games, team1, team2)

# Constants for the event
EVENT_DATE = "2025-06-04"
TEAM1 = "Madison Keys"
TEAM2 = "Coco Gauff"

# Execute the main function and print the recommendation
recommendation = process_event(EVENT_DATE, TEAM1, TEAM2)
print(f"recommendation: {recommendation}")