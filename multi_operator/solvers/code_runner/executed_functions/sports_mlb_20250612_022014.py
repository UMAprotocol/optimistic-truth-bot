import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {str(e)}")
            return None

# Function to check player's score
def check_player_score(date, player_name):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")
    if not games_today:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if "Indiana Pacers" in [game["HomeTeam"], game["AwayTeam"]] and "Oklahoma City Thunder" in [game["HomeTeam"], game["AwayTeam"]]:
            game_id = game["GameID"]
            stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
            if not stats:
                return "p4"  # Unable to retrieve player stats

            for stat in stats:
                if stat["Name"] == player_name:
                    points = stat["Points"]
                    return "p2" if points > 17.5 else "p1"

    return "p1"  # Game not found or player did not play

# Main function to run the check
if __name__ == "__main__":
    game_date = "2025-06-11"
    player = "Tyrese Haliburton"
    recommendation = check_player_score(game_date, player)
    print(f"recommendation: {recommendation}")