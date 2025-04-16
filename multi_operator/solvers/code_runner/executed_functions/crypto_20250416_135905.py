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
    Fetches the result of a UFC match from ESPN or a similar sports data API.

    Args:
        event_date: Date of the event in YYYY-MM-DD format
        fighters: Tuple containing the names of the fighters (fighter1, fighter2)

    Returns:
        Winner's name if available, 'Draw' if a draw, 'Unknown' if no data available.
    """
    logger.info(f"Fetching UFC match result for {fighters[0]} vs {fighters[1]} on {event_date}")
    
    # Convert the event date to UTC timestamp
    try:
        target_time_utc = datetime.strptime(event_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        timestamp = int(target_time_utc.timestamp())
        logger.debug(f"Converted event date to UTC timestamp: {timestamp}")
    except Exception as e:
        logger.error(f"Error converting event date: {e}")
        return "Unknown"

    # API endpoint setup
    api_url = "https://api.sportsdata.io/v3/mma/scores/json/Fight/{timestamp}"
    headers = {
        "Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY
    }

    try:
        logger.debug(f"Requesting data from SportsData.io with timestamp: {timestamp}")
        response = requests.get(api_url.format(timestamp=timestamp), headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Assuming the API returns a list of fights including fighter names and results
        for fight in data:
            if fighters[0] in fight['Fighters'] and fighters[1] in fight['Fighters']:
                if fight['Winner'] == fighters[0]:
                    return fighters[0]
                elif fight['Winner'] == fighters[1]:
                    return fighters[1]
                else:
                    return "Draw"
        
        logger.info("No matching fight found or no winner declared.")
        return "Unknown"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return "Unknown"

def main():
    """
    Main function to handle the UFC fight result query.
    """
    event_date = "2025-04-12"
    fighters = ("Alberto Montes", "Roberto Romero")
    
    logger.info("Processing UFC fight result query")
    
    try:
        result = fetch_ufc_match_result(event_date, fighters)
        
        # Determine the resolution based on the fight result
        if result == fighters[0]:
            recommendation = "p2"  # Montes wins
        elif result == fighters[1]:
            recommendation = "p1"  # Romero wins
        elif result == "Draw":
            recommendation = "p3"  # Draw or no result
        else:
            recommendation = "p3"  # Unknown or no data available
        
        # Output the recommendation
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"Error processing UFC fight result query: {e}")
        # Default to p3 (unknown) in case of any errors
        print("recommendation: p3")

if __name__ == "__main__":
    main()