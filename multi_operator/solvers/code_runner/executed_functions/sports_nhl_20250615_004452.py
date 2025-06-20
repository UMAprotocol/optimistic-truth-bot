import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# Function to make API requests
def make_request(url, tag, is_proxy=False):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if is_proxy:
            print(f"Proxy failed for {tag}, trying primary endpoint.")
            primary_url = url.replace("minimal-ubuntu-production.up.railway.app/binance-proxy", "api.sportsdata.io/v3/nhl")
            return make_request(primary_url, tag)
        else:
            print(f"Failed to retrieve data for {tag}: {str(e)}")
            return None

# Function to check if Brad Marchand scored a goal
def check_goals(game_id):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, "PlayerGameStatsByGame")
    if game_stats:
        for player_stat in game_stats:
            if player_stat["PlayerID"] == 80000302:  # Brad Marchand's PlayerID
                goals = player_stat.get("Goals", 0)
                return "p2" if goals > 0.5 else "p1"
    return "p4"

# Main function to resolve the market
def resolve_market():
    today = datetime.now()
    game_date = datetime(2025, 6, 14, 20)  # Game date and time in ET
    if today > datetime(2025, 12, 31, 23, 59):
        return "p3"  # Resolve to 50-50 if the date is past December 31, 2025

    # Find the game ID for the specific match
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-JUN-14"
    games = make_request(url, "GamesByDate")
    if games:
        for game in games:
            if game["HomeTeam"] == "FLA" and game["AwayTeam"] == "EDM":
                return check_goals(game["GameID"])
    return "p4"

# Run the resolver function and print the recommendation
recommendation = resolve_market()
print(f"recommendation: {recommendation}")