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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Constants for the specific market
MATCH_DATE = "2025-05-31"
PLAYER_NAME = "Calhanoglu Hakan"
TEAMS = ["Paris Saint-Germain", "Inter Milan"]

# Function to get data from API
def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check if player scored in the match
def check_player_score(match_data, player_name):
    for player in match_data.get('PlayerStats', []):
        if player.get('Name') == player_name and player.get('Goals', 0) > 0:
            return True
    return False

# Main function to resolve the market
def resolve_market():
    # Construct URL for the match data
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{MATCH_DATE}"
    match_data = get_data(url, HEADERS)

    if not match_data:
        # Try proxy if primary fails
        url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{MATCH_DATE}"
        match_data = get_data(url, HEADERS)
        if not match_data:
            return "recommendation: p4"  # Unable to resolve due to data fetch failure

    # Check if the match involves the specified teams
    for match in match_data:
        if match['HomeTeam'] in TEAMS and match['AwayTeam'] in TEAMS:
            if datetime.now() < datetime.strptime(MATCH_DATE + " 23:59", "%Y-%m-%d %H:%M"):
                return "recommendation: p4"  # Match has not been completed
            if check_player_score(match, PLAYER_NAME):
                return "recommendation: p2"  # Player scored
            else:
                return "recommendation: p1"  # Player did not score

    # If no relevant match found
    return "recommendation: p3"  # 50-50 if match not found or not completed by end of year

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)