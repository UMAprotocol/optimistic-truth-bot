import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
ROLAND_GARROS_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")  # Assuming tennis data is under CBB for this example

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": ROLAND_GARROS_API_KEY}

def get_player_status(player_name):
    """
    Check if the player has reached the quarterfinals in the French Open.
    """
    today = datetime.now().date()
    url = f"{PROXY_ENDPOINT}/scores/json/PlayerSeasonStatsByPlayer/{today.year}/{player_name}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url.replace(PROXY_ENDPOINT, PRIMARY_ENDPOINT), headers=HEADERS, timeout=10)
        
        data = response.json()
        # Assuming the data structure includes a 'stage' key that tells us the current tournament stage of the player
        if 'stage' in data and data['stage'] == 'Quarterfinals':
            return "p2"  # Yes, reached quarterfinals
        else:
            return "p1"  # No, did not reach quarterfinals
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    player_name = "Grigor Dimitrov"
    recommendation = get_player_status(player_name)
    print(f"recommendation: {recommendation}")