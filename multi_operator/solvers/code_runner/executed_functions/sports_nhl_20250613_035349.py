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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-12"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"EDM": "p2", "FLA": "p1", "50-50": "p3", "Too early to resolve": "p4"}

# Helper function to make API requests
def make_request(url, headers, timeout=10):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

# Main function to determine the outcome
def resolve_market():
    # Construct URL for game data
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    game_data = make_request(url, HEADERS)

    if not game_data:
        # Fallback to proxy if primary fails
        url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
        game_data = make_request(url, HEADERS)
        if not game_data:
            return "recommendation: p4"  # Unable to retrieve data

    # Find the specific game
    for game in game_data:
        if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
            if game["Status"] == "Final":
                # Check if Connor McDavid scored
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{game['GameID']}"
                player_stats = make_request(player_stats_url, HEADERS)
                if player_stats:
                    for stat in player_stats:
                        if stat["PlayerID"] == 8478402:  # Connor McDavid's PlayerID
                            goals = stat.get("Goals", 0)
                            if goals > 0.5:
                                return "recommendation: p2"  # Scored more than 0.5 goals
                            else:
                                return "recommendation: p1"  # Did not score more than 0.5 goals
            elif game["Status"] in ["Scheduled", "InProgress"]:
                return "recommendation: p4"  # Game not completed
            elif game["Status"] in ["Postponed", "Canceled"]:
                return "recommendation: p3"  # Game not played by the deadline
    return "recommendation: p4"  # Game not found or other issues

# Execute the function and print the result
if __name__ == "__main__":
    print(resolve_market())