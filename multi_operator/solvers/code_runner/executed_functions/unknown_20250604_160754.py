import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PGA_TOUR_API_KEY = os.getenv("PGA_TOUR_API_KEY")

# Constants
TOURNAMENT_START_DATE = "2025-05-29"
TOURNAMENT_END_DATE = "2025-06-01"
SCOTTIE_SCHEFFLER = "Scottie Scheffler"
XANDER_SCHAUFFELE = "Xander Schauffele"
PGA_TOUR_ENDPOINT = "https://api.pgatour.com/api/v1"

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {PGA_TOUR_API_KEY}"
}

# Function to get tournament results
def get_tournament_results():
    url = f"{PGA_TOUR_ENDPOINT}/tournament_results?start_date={TOURNAMENT_START_DATE}&end_date={TOURNAMENT_END_DATE}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to retrieve tournament results")

# Function to determine the outcome
def determine_outcome(results):
    scheffler_position = None
    schauffele_position = None

    for player in results['players']:
        if player['name'] == SCOTTIE_SCHEFFLER:
            scheffler_position = player['position']
        elif player['name'] == XANDER_SCHAUFFELE:
            schauffele_position = player['position']

    if scheffler_position is None or schauffele_position is None:
        return "p4"  # In case data is missing

    if scheffler_position < schauffele_position:
        return "p2"  # Scheffler wins
    elif schauffele_position < scheffler_position:
        return "p1"  # Schauffele wins
    else:
        return "p3"  # Tie

# Main execution block
if __name__ == "__main__":
    try:
        results = get_tournament_results()
        recommendation = determine_outcome(results)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")  # Default to unresolved if there's an error