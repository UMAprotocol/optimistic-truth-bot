import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the API key for Sports Data IO from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

def fetch_chess_match_result():
    # Define the URL for the API endpoint
    # Note: This is a hypothetical endpoint as Sports Data IO does not provide chess data.
    # Replace this with the actual API endpoint for chess data.
    url = "https://api.sportsdata.io/v3/chess/scores/json/PlayerSeasonStats/2025"

    # Set up the headers with the API key
    headers = {
        'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_MLB_API_KEY
    }

    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP error codes

        # Process the response data
        data = response.json()

        # Check the results for the specific match between Erigaisi and Nakamura
        for match in data:
            if match['Player1'] == 'Arjun Erigaisi' and match['Player2'] == 'Hikaru Nakamura':
                if match['Winner'] == 'Arjun Erigaisi':
                    return 'recommendation: p2'  # Erigaisi advances
                elif match['Winner'] == 'Hikaru Nakamura':
                    return 'recommendation: p1'  # Nakamura advances

        # If no specific result is found, assume the match is yet to be completed
        return 'recommendation: p3'  # Unknown/50-50 if canceled or no data

    except requests.RequestException as e:
        # Handle any errors that occur during the API request
        print(f"An error occurred: {e}")
        return 'recommendation: p3'  # Unknown/50-50 if error occurs

# Run the function and print the result
result = fetch_chess_match_result()
print(result)