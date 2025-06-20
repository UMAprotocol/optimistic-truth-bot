import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
DATE_OF_MATCH = "2025-06-19"
PLAYER1 = "Felix Auger-Aliassime"
PLAYER2 = "Karen Khachanov"
TOURNAMENT_URL = "https://www.terrawortmann-open.de/en/"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Resolution map based on the outcome
RESOLUTION_MAP = {
    PLAYER1: "p2",  # Auger-Aliassime wins
    PLAYER2: "p1",  # Khachanov wins
    "50-50": "p3",  # Tie, canceled, or delayed
    "Too early to resolve": "p4"
}

def get_match_result():
    # Simulate fetching data from the tournament website
    # This is a placeholder for the actual API call or web scraping logic
    # In practice, you would fetch and parse the actual tournament results
    # Here we assume the match result is directly available as a string
    # Example: "Felix Auger-Aliassime advances against Karen Khachanov"
    # For demonstration, we simulate a result
    simulated_result = "Felix Auger-Aliassime advances against Karen Khachanov"
    return simulated_result

def resolve_market(result):
    if "advances against" in result:
        winner = result.split(" advances against")[0]
        return "recommendation: " + RESOLUTION_MAP.get(winner, "p4")
    elif "canceled" in result.lower() or "delayed" in result.lower():
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    match_result = get_match_result()
    resolution = resolve_market(match_result)
    print(resolution)