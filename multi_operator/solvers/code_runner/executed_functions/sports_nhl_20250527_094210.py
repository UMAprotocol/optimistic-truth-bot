import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"
DATE_OF_GAME = "2025-05-26"
TEAMS = {"Hurricanes": "CAR", "Panthers": "FLA"}
RESOLUTION_MAP = {"CAR": "p2", "FLA": "p1", "50-50": "p3", "Too early to resolve": "p4"}

# Function to get data from API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game():
    # Try proxy endpoint first
    games = get_data(f"{PROXY_ENDPOINT}/GamesByDate/{DATE_OF_GAME}")
    if not games:
        # Fallback to primary endpoint
        games = get_data(f"{PRIMARY_ENDPOINT}/GamesByDate/{DATE_OF_GAME}")

    if not games:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games:
        if game["Status"] == "Canceled":
            return "recommendation: p3"
        if game["Status"] == "Postponed":
            # Check if the game date is today or in the past
            game_date = datetime.strptime(game["Day"], "%Y-%m-%dT%H:%M:%S")
            if game_date.date() > datetime.utcnow().date():
                return "recommendation: p4"
            else:
                continue  # Game postponed but still within the date range
        if game["Status"] == "Final":
            home_team = game["HomeTeam"]
            away_team = game["AwayTeam"]
            home_score = game["HomeTeamScore"]
            away_score = game["AwayTeamScore"]
            if home_score == away_score:
                return "recommendation: p3"  # Tie game, resolve as 50-50
            winner = home_team if home_score > away_score else away_team
            return f"recommendation: {RESOLUTION_MAP.get(winner, 'p4')}"

    return "recommendation: p4"  # No relevant game found or game not yet played

# Main execution
if __name__ == "__main__":
    print(resolve_game())