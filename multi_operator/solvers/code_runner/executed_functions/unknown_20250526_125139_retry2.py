import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(PROXY_ENDPOINT, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_mlb_game(date, team1, team2):
    date_formatted = datetime.strptime(date, "%Y-%m-%d").date()
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games_data = get_data(games_url, HEADERS)

    if games_data:
        for game in games_data:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    home_score = game["HomeTeamRuns"]
                    away_score = game["AwayTeamRuns"]
                    if home_score > away_score:
                        return "p1" if game["HomeTeam"] == team1 else "p2"
                    elif away_score > home_score:
                        return "p1" if game["AwayTeam"] == team1 else "p2"
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return "p3"
        return "p4"  # Game not found or not final
    return "p4"  # No data available or error

# Example usage
if __name__ == "__main__":
    # Example game details
    game_date = "2025-04-23"
    team1 = "Texas Rangers"
    team2 = "Oakland Athletics"

    recommendation = resolve_mlb_game(game_date, team1, team2)
    print(f"recommendation: {recommendation}")