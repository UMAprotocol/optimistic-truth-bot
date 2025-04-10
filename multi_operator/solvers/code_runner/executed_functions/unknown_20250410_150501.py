import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the API key for Sports Data IO from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# Define the URL and headers for the Sports Data IO API
API_URL = "https://api.sportsdata.io/v3/chess/scores/json/PlayerSeasonStats/2025"
HEADERS = {
    'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_MLB_API_KEY
}

def fetch_chess_data():
    """
    Fetches chess data from the Sports Data IO API and processes it to determine the outcome of the match.
    """
    try:
        # Make the API call
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Process the response data
        data = response.json()
        for match in data:
            if match['Tournament'] == 'Freestyle Chess Grand Slam Paris' and match['Round'] == 'Quarterfinal':
                if 'Maxime Vachier-Lagrave' in match['Players'] and match['Outcome'] == 'Advanced':
                    return 'recommendation: p2'  # Vachier-Lagrave advances
                elif 'Fabiano Caruana' in match['Players'] and match['Outcome'] == 'Advanced':
                    return 'recommendation: p1'  # Caruana advances

        # If no match found or no player advanced
        return 'recommendation: p3'  # Unknown or 50-50 if canceled

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return 'recommendation: p3'  # Unknown or 50-50 in case of error

# Run the function and print the result
result = fetch_chess_data()
print(result)