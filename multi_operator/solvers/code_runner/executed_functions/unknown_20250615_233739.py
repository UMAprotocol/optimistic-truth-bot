import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PGA_TOUR_API_KEY = os.getenv("PGA_TOUR_API_KEY")

# Constants
PGA_TOUR_ENDPOINT = "https://api.pgatour.com/api/v1"
PGA_TOUR_PROXY = "https://minimal-ubuntu-production.up.railway.app/pgatour-proxy"

# Headers for API requests
HEADERS = {"Authorization": f"Bearer {PGA_TOUR_API_KEY}"}

# Function to fetch data from PGA Tour API with fallback to proxy
def fetch_pga_tour_data(endpoint, params):
    try:
        response = requests.get(f"{PGA_TOUR_ENDPOINT}/{endpoint}", headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Primary endpoint failed with status {response.status_code}. Trying proxy...")
            response = requests.get(f"{PGA_TOUR_PROXY}/{endpoint}", headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Proxy endpoint also failed with status {response.status_code}.")
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
    return None

# Function to determine the outcome based on the fetched data
def determine_outcome(data, player1, player2):
    if not data:
        return "p4"  # Unable to fetch data

    player1_score = next((player['score'] for player in data if player['name'] == player1), None)
    player2_score = next((player['score'] for player in data if player['name'] == player2), None)

    if player1_score is None or player2_score is None:
        return "p4"  # Player data missing

    if player1_score < player2_score:
        return "p1"  # Player 1 has a better score
    elif player2_score < player1_score:
        return "p2"  # Player 2 has a better score
    else:
        return "p3"  # Scores are tied

# Main function to execute the logic
def main():
    today = datetime.now().strftime("%Y-%m-%d")
    data = fetch_pga_tour_data("leaderboard", {"tournament": "US Open", "date": today})
    result = determine_outcome(data, "Scottie Scheffler", "Rory McIlroy")
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()