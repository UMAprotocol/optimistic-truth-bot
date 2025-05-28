import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Casper Ruud reached the quarterfinals
def check_ruud_quarterfinals():
    today = datetime.now().strftime("%Y-%m-%d")
    url = PRIMARY_ENDPOINT + today
    games_today = make_request(url, HEADERS)

    if games_today is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games_today = make_request(PROXY_ENDPOINT, HEADERS)
        if games_today is None:
            return "recommendation: p4"  # Unable to retrieve data

    # Check if Casper Ruud's match is among today's games and if he reached quarterfinals
    for game in games_today:
        if "Casper Ruud" in game['Players'] and game['Round'] == 'Quarterfinals':
            return "recommendation: p2"  # Yes, he reached the quarterfinals
        elif "Casper Ruud" in game['Players'] and game['Round'] != 'Quarterfinals':
            return "recommendation: p1"  # No, he did not reach the quarterfinals

    return "recommendation: p4"  # No data available for today's date or not yet played

# Main execution
if __name__ == "__main__":
    result = check_ruud_quarterfinals()
    print(result)