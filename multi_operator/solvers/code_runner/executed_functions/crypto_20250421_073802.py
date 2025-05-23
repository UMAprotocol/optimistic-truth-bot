import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Endpoint configurations
ESPN_API_ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"

def fetch_ufc_match_result(event_date, fighter1, fighter2):
    """
    Fetches the result of a UFC match between two fighters on a specific date from ESPN API.
    
    Args:
        event_date (str): The date of the event in YYYY-MM-DD format.
        fighter1 (str): Name of the first fighter.
        fighter2 (str): Name of the second fighter.
    
    Returns:
        str: 'Elder' if Evan Elder wins, 'Hassanzada' if Ahmad Hassanzada wins, 'Draw' if it's a draw.
    """
    try:
        # Convert event date to datetime object
        event_datetime = datetime.strptime(event_date, "%Y-%m-%d")
        # Format date for the API call
        formatted_date = event_datetime.strftime("%Y%m%d")
        
        # Make the API request
        response = requests.get(f"{ESPN_API_ENDPOINT}?dates={formatted_date}")
        response.raise_for_status()
        data = response.json()
        
        # Search for the match result
        for event in data.get('events', []):
            competitors = event.get('competitions', [])[0].get('competitors', [])
            fighter1_result = next((comp for comp in competitors if fighter1 in comp.get('athlete', {}).get('displayName', '')), None)
            fighter2_result = next((comp for comp in competitors if fighter2 in comp.get('athlete', {}).get('displayName', '')), None)
            
            if fighter1_result and fighter2_result:
                if fighter1_result['winner']:
                    return 'Elder'
                elif fighter2_result['winner']:
                    return 'Hassanzada'
                else:
                    return 'Draw'
        
        return 'Unknown'  # If no match found or data is incomplete
    except Exception as e:
        print(f"Failed to fetch or parse data: {e}")
        return 'Unknown'

def main():
    # Specific event details
    event_date = "2025-04-27"
    fighter1 = "Evan Elder"
    fighter2 = "Ahmad Hassanzada"
    
    # Fetch the match result
    result = fetch_ufc_match_result(event_date, fighter1, fighter2)
    
    # Determine the resolution based on the result
    if result == 'Elder':
        print("recommendation: p2")
    elif result == 'Hassanzada':
        print("recommendation: p1")
    elif result == 'Draw':
        print("recommendation: p3")
    else:
        print("recommendation: p3")  # Default to 50-50 if result is unknown or match not found

if __name__ == "__main__":
    main()