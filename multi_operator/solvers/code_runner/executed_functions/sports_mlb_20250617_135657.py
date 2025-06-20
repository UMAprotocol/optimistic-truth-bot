import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants for the match
MATCH_DATE = "2025-06-17"
PLAYER1 = "Joao Fonseca"
PLAYER2 = "Flavio Cobolli"
TOURNAMENT_URL = "https://www.terrawortmann-open.de/en/"

# Function to fetch match data
def fetch_match_data():
    try:
        response = requests.get(TOURNAMENT_URL, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to parse and determine the outcome
def determine_outcome(html_data):
    if not html_data:
        return "p3"  # Assume 50-50 if data cannot be fetched

    if PLAYER1 in html_data and PLAYER2 in html_data:
        if "advances" in html_data and PLAYER1 in html_data:
            return "p2"  # Fonseca wins
        elif "advances" in html_data and PLAYER2 in html_data:
            return "p1"  # Cobolli wins
    return "p3"  # Default to 50-50 if unclear

# Main function to run the resolution logic
def main():
    html_data = fetch_match_data()
    outcome = determine_outcome(html_data)
    print(f"recommendation: {outcome}")

if __name__ == "__main__":
    main()