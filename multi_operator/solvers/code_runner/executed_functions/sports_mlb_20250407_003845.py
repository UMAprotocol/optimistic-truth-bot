from dotenv import load_dotenv
import os
import requests

def check_spurs_playoff_status():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
    if not api_key:
        return "recommendation: p3"  # Unable to resolve due to missing API key

    try:
        response = requests.get(
            "https://api.sportsdata.io/v3/nba/scores/json/Standings/2025",
            headers={"Ocp-Apim-Subscription-Key": api_key}
        )
        standings = response.json()

        # Check if the Spurs are in the top 8 of their conference
        for team in standings:
            if team['Team'] == 'SAS' and team['ConferenceRank'] <= 8:
                return "recommendation: p2"  # Spurs make the playoffs
        return "recommendation: p1"  # Spurs do not make the playoffs

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return "recommendation: p3"  # Unable to resolve due to API error
    except KeyError:
        print("Error processing data from API.")
        return "recommendation: p3"  # Unable to resolve due to data error

# Example usage
result = check_spurs_playoff_status()
print(result)