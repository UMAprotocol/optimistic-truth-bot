import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
PGA_TOUR_API_KEY = os.getenv("PGA_TOUR_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-15"
SCOTTIE_SCHEFFLER = "Scottie Scheffler"
RORY_MCILROY = "Rory McIlroy"
PGA_TOUR_ENDPOINT = "https://api.pgatour.com/api/v1"
PGA_TOUR_PROXY = "https://minimal-ubuntu-production.up.railway.app/pgatour-proxy"

# Headers for API requests
HEADERS = {"Authorization": f"Bearer {PGA_TOUR_API_KEY}"}

# Function to fetch data from PGA Tour API with fallback to proxy
def fetch_pga_tour_data(endpoint, proxy, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch from primary endpoint, status code: {response.status_code}. Trying proxy...")
            response = requests.get(f"{proxy}{path}", headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch from proxy endpoint, status code: {response.status_code}.")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to determine the outcome based on the fetched data
def determine_outcome(data):
    if not data:
        return "p4"  # Unable to fetch data

    scheffler_position = None
    mcilroy_position = None

    # Extract positions from the data
    for player in data.get('players', []):
        if player['name'] == SCOTTIE_SCHEFFLER:
            scheffler_position = player['position']
        elif player['name'] == RORY_MCILROY:
            mcilroy_position = player['position']

    if scheffler_position is None or mcilroy_position is None:
        return "p4"  # Data incomplete

    # Compare positions
    if scheffler_position < mcilroy_position:
        return "p2"  # Scheffler wins
    elif mcilroy_position < scheffler_position:
        return "p1"  # McIlroy wins
    else:
        return "p3"  # Tie

# Main function to run the market resolution
def main():
    path = f"/tournament/{EVENT_DATE}/results"
    data = fetch_pga_tour_data(PGA_TOUR_ENDPOINT, PGA_TOUR_PROXY, path)
    result = determine_outcome(data)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()