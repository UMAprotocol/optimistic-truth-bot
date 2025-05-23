import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
SPORTS_DATA_IO_NFL_API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
SPORTS_DATA_IO_NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for the UFC event
EVENT_DATE = "2025-04-27"
UFC_FIGHT_NIGHT_URL = "https://api.sportsdata.io/v3/mma/scores/json/Schedule/UFC"
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_NFL_API_KEY}

def fetch_ufc_event_results():
    try:
        response = requests.get(UFC_FIGHT_NIGHT_URL, headers=HEADERS)
        response.raise_for_status()
        events = response.json()
        
        for event in events:
            if event['Day'] == EVENT_DATE:
                for fight in event['Fights']:
                    if fight['Fighter1LastName'] == "Elder" and fight['Fighter2LastName'] == "Hassanzada":
                        if fight['Winner'] == "Elder":
                            return "p2"  # Elder wins
                        elif fight['Winner'] == "Hassanzada":
                            return "p1"  # Hassanzada wins
                        else:
                            return "p3"  # Draw or no result
        return "p3"  # No specific fight result found for the given date
    except requests.RequestException as e:
        print(f"Failed to fetch UFC event results: {e}")
        return "p3"  # Resolve to unknown/50-50 if there is an error

def main():
    result = fetch_ufc_event_results()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()