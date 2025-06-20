import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HSBC_CHAMPIONSHIPS_URL = "https://www.lta.org.uk/fan-zone/international/hsbc-championships/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
MATCH_DATE = "2025-06-17"
PLAYER1 = "Alex De Minaur"
PLAYER2 = "Jiri Lehecka"

# Resolution map
RESOLUTION_MAP = {
    PLAYER1: "p2",  # De Minaur wins
    PLAYER2: "p1",  # Lehecka wins
    "50-50": "p3",  # Tie, canceled, or delayed
    "unknown": "p4"  # Not enough data
}

def get_match_result():
    try:
        response = requests.get(HSBC_CHAMPIONSHIPS_URL, timeout=10)
        if response.status_code == 200:
            # Simulated parsing logic (actual logic depends on the page structure)
            if PLAYER1 in response.text and "advances" in response.text:
                return PLAYER1
            elif PLAYER2 in response.text and "advances" in response.text:
                return PLAYER2
            elif "canceled" in response.text or "delayed" in response.text:
                return "50-50"
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return "unknown"
    except requests.RequestException as e:
        print(f"Error during requests to {HSBC_CHAMPIONSHIPS_URL}: {str(e)}")
        return "unknown"

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    if today > MATCH_DATE:
        result = get_match_result()
        recommendation = RESOLUTION_MAP.get(result, "p4")
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")  # Match has not occurred yet or is in progress