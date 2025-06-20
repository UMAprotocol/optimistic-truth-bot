import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to check if Carter Verhaeghe scored a goal
def check_player_goals(game_id, player_name):
    game_stats = make_request(f"/scores/json/PlayerGameStatsByGame/{game_id}")
    if game_stats:
        for player in game_stats:
            if player["Name"] == player_name and player["Goals"] > 0:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    today_date = datetime.now().strftime("%Y-%m-%d")
    games_today = make_request(f"/scores/json/GamesByDate/{today_date}")
    if games_today:
        for game in games_today:
            if game["Status"] == "Final" and {"Edmonton Oilers", "Florida Panthers"} == {game["HomeTeam"], game["AwayTeam"]}:
                if check_player_goals(game["GameID"], "Carter Verhaeghe"):
                    return RESOLUTION_MAP["Yes"]
                else:
                    return RESOLUTION_MAP["No"]
    return RESOLUTION_MAP["50-50"]

# Run the main function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")