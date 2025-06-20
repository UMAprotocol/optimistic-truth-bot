import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
BOSS_OPEN_URL = "https://bossopen.com/en/home"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to get match result
def get_match_result():
    # Define the date range for the match
    match_date = datetime.strptime("2025-06-12", "%Y-%m-%d")
    end_date = datetime.strptime("2025-07-12", "%Y-%m-%d")

    # Check the match result within the date range
    current_date = datetime.now()
    if current_date < match_date:
        return "p4"  # Match has not occurred yet
    elif current_date > end_date:
        return "p3"  # Match delayed beyond the allowed date range

    # Attempt to fetch match data from the primary source
    try:
        response = requests.get(BOSS_OPEN_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        match_data = response.json()

        # Check if the match was canceled or ended in a tie
        if match_data.get('status') in ['canceled', 'tie']:
            return "p3"

        # Determine the winner
        if match_data.get('winner') == 'Alex Michelsen':
            return "p2"  # Michelsen wins
        elif match_data.get('winner') == 'Justin Engel':
            return "p1"  # Engel wins

    except requests.RequestException as e:
        print(f"Failed to fetch data from primary source: {e}")
        return "p3"  # Resolve as unknown/50-50 due to data fetch failure

    return "p3"  # Default to unknown/50-50 if no clear outcome

# Main execution
if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")