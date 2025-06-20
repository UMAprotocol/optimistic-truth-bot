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

# Date and team information
GAME_DATE = "2025-06-19"
PLAYER_NAME = "Shai Gilgeous-Alexander"
TEAM_ABBREVIATION = "OKC"  # Oklahoma City Thunder

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

# Function to find the game and check player's points
def check_player_points():
    date_str = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(f"/scores/json/GamesByDate/{date_str}", use_proxy=True)
    if not games:
        return "p4"  # Unable to retrieve data

    for game in games:
        if game['Status'] == "Scheduled" and (game['HomeTeam'] == TEAM_ABBREVIATION or game['AwayTeam'] == TEAM_ABBREVIATION):
            # Check if the game is the correct one and if SGA played
            game_id = game['GameID']
            stats = make_request(f"/stats/json/PlayerGameStatsByGame/{game_id}", use_proxy=True)
            if not stats:
                return "p4"  # Unable to retrieve player stats

            for stat in stats:
                if stat['Name'] == PLAYER_NAME:
                    points = stat.get('Points', 0)
                    return "p2" if points > 34.5 else "p1"

    return "p1"  # Game not found or player did not play

# Main execution
if __name__ == "__main__":
    recommendation = check_player_points()
    print(f"recommendation: {recommendation}")