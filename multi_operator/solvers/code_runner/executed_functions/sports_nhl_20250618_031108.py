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
GAME_DATE = "2025-06-17"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"EDM": "p1", "FLA": "p2", "50-50": "p3", "Too early to resolve": "p4"}

# Helper function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Sam Bennett scored a goal
def check_goals(player_stats):
    for stat in player_stats:
        if stat["PlayerID"] == 8477934 and stat["Goals"] > 0:  # Sam Bennett's PlayerID
            return True
    return False

# Main function to resolve the market
def resolve_market():
    # Construct URL for game data
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"

    # Make the request to the proxy endpoint
    games = make_request(url, HEADERS)
    if not games:  # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"
        games = make_request(url, HEADERS)

    if not games:
        return "recommendation: p4"  # Unable to retrieve data

    # Find the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {"EDM", "FLA"}:
            if game["Status"] == "Final":
                # Check player stats
                game_id = game["GameID"]
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(player_stats_url, HEADERS)
                if player_stats and check_goals(player_stats):
                    return "recommendation: p2"  # Sam Bennett scored
                else:
                    return "recommendation: p1"  # Sam Bennett did not score
            else:
                return "recommendation: p4"  # Game not completed
    return "recommendation: p3"  # Game not found or not scheduled

# Execute the function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)