import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Constants
NBA_FINALS_END_DATE = datetime(2025, 7, 22, 23, 59)  # July 22, 2025, 11:59 PM ET

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Function to check if any player scored 40+ points
def check_high_scores():
    current_date = datetime.now()
    if current_date > NBA_FINALS_END_DATE:
        return "recommendation: p3"  # Market resolves 50-50 if beyond the end date

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, "/scores/json/GamesByDate/2025")
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, "/scores/json/GamesByDate/2025")

    if games:
        for game in games:
            for player_stats in game.get('PlayerStats', []):
                if player_stats.get('Points', 0) > 39.5:
                    return "recommendation: p2"  # Yes, a player scored 40+ points
        return "recommendation: p1"  # No player scored 40+ points
    else:
        return "recommendation: p4"  # Unable to retrieve data or in-progress

# Main execution
if __name__ == "__main__":
    result = check_high_scores()
    print(result)