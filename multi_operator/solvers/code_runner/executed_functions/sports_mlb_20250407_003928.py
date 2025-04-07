import requests
from dotenv import load_dotenv
import os

def check_spurs_playoff_status():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
    if not api_key:
        return "recommendation: p3"  # Unable to resolve due to missing API key

    try:
        url = "https://api.sportsdata.io/v3/nba/scores/json/Standings/2025"
        headers = {
            'Ocp-Apim-Subscription-Key': api_key
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        standings = response.json()

        # Check if Spurs are in the top 8 of their conference
        for team in standings:
            if team['Team'] == 'SA' and team['ConferenceRank'] and int(team['ConferenceRank']) <= 8:
                return "recommendation: p2"  # Spurs made the playoffs

        # If not found in top 8 or not listed
        return "recommendation: p1"  # Spurs did not make the playoffs

    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return "recommendation: p3"  # Unable to resolve due to API error
    except KeyError:
        print("Error processing data from API.")
        return "recommendation: p3"  # Data format error or missing data

# Run the function and print the result
result = check_spurs_playoff_status()
print(result)