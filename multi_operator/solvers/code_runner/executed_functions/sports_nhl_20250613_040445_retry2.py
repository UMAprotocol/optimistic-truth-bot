import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API access
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to fetch data from API with fallback to proxy
def fetch_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to proxy if primary fails
            response = requests.get(PROXY_ENDPOINT + url, headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check if Corey Perry scored in the game
def check_corey_perry_score(game_id):
    url = f"{PRIMARY_ENDPOINT}/scores/json/BoxScore/{game_id}"
    data = fetch_data(url)
    if data:
        for player in data['PlayerStats']:
            if player['Name'] == "Corey Perry" and player['Goals'] > 0:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    # Define the game date and time
    game_date = "2025-06-12"
    game_time = "20:00:00"
    datetime_format = "%Y-%m-%d %H:%M:%S"
    game_datetime = datetime.strptime(f"{game_date} {game_time}", datetime_format)

    # Current time for comparison
    current_datetime = datetime.now()

    # Check if the game has not yet occurred
    if current_datetime < game_datetime:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Fetch scheduled games on the game date
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = fetch_data(url)
    if games:
        for game in games:
            if game['Status'] == "Final" and "Edmonton Oilers" in game['Teams'] and "Florida Panthers" in game['Teams']:
                if check_corey_perry_score(game['GameID']):
                    return "recommendation: " + RESOLUTION_MAP["Yes"]
                else:
                    return "recommendation: " + RESOLUTION_MAP["No"]

    # If the game date has passed and no valid game data found, assume 50-50
    if current_datetime > datetime.strptime(f"{game_date} 23:59:59", datetime_format):
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    # Default to 50-50 if no other condition is met
    return "recommendation: " + RESOLUTION_MAP["50-50"]

# Execute the main function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)