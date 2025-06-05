import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
PGA_TOUR_API_KEY = os.getenv("PGA_TOUR_API_KEY")

# Constants
TOURNAMENT_START_DATE = "2025-05-29"
TOURNAMENT_END_DATE = "2025-06-01"
TOURNAMENT_URL = "https://api.pgatour.com/api/v3"

# Helper functions
def get_tournament_results():
    url = f"{TOURNAMENT_URL}/tournament_results?start_date={TOURNAMENT_START_DATE}&end_date={TOURNAMENT_END_DATE}"
    headers = {"Authorization": f"Bearer {PGA_TOUR_API_KEY}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch tournament results")

def resolve_market(scheffler_position, schauffele_position):
    if scheffler_position < schauffele_position:
        return "p2"  # Scheffler wins
    elif schauffele_position < scheffler_position:
        return "p1"  # Schauffele wins
    else:
        return "p3"  # Tie

# Main execution
if __name__ == "__main__":
    try:
        results = get_tournament_results()
        scheffler_position = next(player['position'] for player in results if player['player_name'] == "Scottie Scheffler")
        schauffele_position = next(player['position'] for player in results if player['player_name'] == "Xander Schauffele")
        recommendation = resolve_market(scheffler_position, schauffele_position)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")  # Unable to resolve due to error