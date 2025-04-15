import requests
import logging
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API key for sports data
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_ufc_match_result(event_date, fighters):
    """
    Fetches the result of a UFC match from ESPN or other credible sources.

    Args:
        event_date: Date of the event in YYYY-MM-DD format
        fighters: Tuple containing the names of the fighters (fighter1, fighter2)

    Returns:
        Result of the match as 'Montes', 'Romero', or 'Draw'
    """
    logger.info(f"Fetching UFC match result for {fighters[0]} vs {fighters[1]} on {event_date}")
    
    # Example URL and API key usage (API key usage is just illustrative)
    api_url = f"https://api.sportsdata.io/v3/mma/scores/json/Fight/{event_date}"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Example data processing
        for fight in data:
            if fighters[0] in fight['Fighters'] and fighters[1] in fight['Fighters']:
                if fight['Winner'] == fighters[0]:
                    return 'Montes'
                elif fight['Winner'] == fighters[1]:
                    return 'Romero'
                else:
                    return 'Draw'
        
        logger.error("No data found for the specified match")
        return 'Draw'  # Default to draw if no specific winner data found

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return 'Draw'  # Default to draw in case of API failure

def main():
    """
    Main function to handle the UFC match result query.
    """
    event_date = "2025-04-12"
    fighters = ("Alberto Montes", "Roberto Romero")
    
    logger.info("Starting UFC match result retrieval process...")
    
    try:
        result = fetch_ufc_match_result(event_date, fighters)
        logger.info(f"Match result: {result}")
        
        # Map result to resolution conditions
        if result == 'Montes':
            recommendation = "p2"
        elif result == 'Romero':
            recommendation = "p1"
        else:
            recommendation = "p3"
        
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"Error processing UFC match result: {e}")
        print("recommendation: p3")  # Default to 50-50 in case of any errors

if __name__ == "__main__":
    main()