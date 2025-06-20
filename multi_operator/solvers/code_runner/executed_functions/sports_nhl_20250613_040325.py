import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Corey Perry"
TEAM_ABBREVIATIONS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# Function to make API requests
def make_request(url, tag, is_proxy=False):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if is_proxy:
            print(f"Proxy failed for {tag}, trying primary endpoint.")
            return None
        else:
            print(f"HTTP Error for {tag}: {str(e)}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {tag}: {str(e)}")
        return None

# Function to find the game and check if Corey Perry scored
def check_player_score():
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{formatted_date}"

    # Try proxy first
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"
    games = make_request(proxy_url, "GamesByDate via Proxy", is_proxy=True)
    if games is None:
        games = make_request(url, "GamesByDate")

    if games:
        for game in games:
            if game['HomeTeam'] in TEAM_ABBREVIATIONS and game['AwayTeam'] in TEAM_ABBREVIATIONS:
                game_id = game['GameID']
                # Fetch players stats for the game
                player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(player_stats_url, "PlayerGameStatsByGame")
                if player_stats:
                    for player_stat in player_stats:
                        if player_stat['Name'] == PLAYER_NAME:
                            goals = player_stat['Goals']
                            if goals > 0.5:
                                return "p2"  # Yes, scored more than 0.5 goals
                            else:
                                return "p1"  # No, did not score more than 0.5 goals
    return "p3"  # 50-50 if game not found or no data available

# Main execution
if __name__ == "__main__":
    result = check_player_score()
    print(f"recommendation: {result}")