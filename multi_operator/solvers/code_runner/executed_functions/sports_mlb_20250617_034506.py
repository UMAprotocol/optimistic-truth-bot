import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
NBA_FINALS_END_DATE = datetime(2025, 7, 22, 23, 59)
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to get game data
def get_nba_finals_data():
    try:
        response = requests.get(
            "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-06-01",  # Example date
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching NBA Finals data: {e}")
        return None

# Analyze game data to determine if any player scored 40+ points
def analyze_game_data(games):
    if not games:
        return "p4"  # Unable to fetch data
    for game in games:
        for player_stats in game.get('PlayerStats', []):
            if player_stats.get('Points', 0) > 39.5:
                return "p2"  # Yes, a player scored 40+ points
    return "p1"  # No player scored 40+ points

# Main function to resolve the market
def resolve_market():
    current_time = datetime.now()
    if current_time > NBA_FINALS_END_DATE:
        return "p3"  # Market resolves 50-50 if beyond the final date

    games = get_nba_finals_data()
    recommendation = analyze_game_data(games)
    return f"recommendation: {recommendation}"

# Run the resolver
if __name__ == "__main__":
    result = resolve_market()
    print(result)