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
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Connor McDavid scored in the specified game
def check_mcdavid_score(game_date, team1, team2):
    formatted_date = game_date.strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    # Check player stats
                    game_id = game['GameID']
                    player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                    player_stats = make_request(player_stats_url, HEADERS)
                    if player_stats:
                        for player_stat in player_stats:
                            if player_stat['Name'] == "Connor McDavid" and player_stat['Goals'] > 0:
                                return "Yes"
                    return "No"
                else:
                    return "50-50"
    return "50-50"

# Main function to run the check
def main():
    game_date = datetime(2025, 6, 12)
    team1 = "EDM"  # Edmonton Oilers
    team2 = "FLA"  # Florida Panthers
    result = check_mcdavid_score(game_date, team1, team2)
    recommendation = RESOLUTION_MAP.get(result, "p3")  # Default to "50-50" if result is not found
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()