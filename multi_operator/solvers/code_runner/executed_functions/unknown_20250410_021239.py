import os
import requests
from dotenv import load_dotenv

def fetch_nhl_game_result():
    # Load environment variables
    load_dotenv()

    # API key for Sports Data IO
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

    # Define the API endpoint
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-09"

    # Set up headers with the API key
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses

        # Parse the JSON response
        games = response.json()

        # Define teams for the game in question
        team_a = "Philadelphia Flyers"
        team_b = "New York Rangers"

        # Search for the specific game
        for game in games:
            if team_a in game['HomeTeam'] and team_b in game['AwayTeam'] or team_a in game['AwayTeam'] and team_b in game['HomeTeam']:
                if game['Status'] == "Final":
                    # Determine the winner
                    if game['HomeTeam'] == team_a and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"  # Flyers win
                    elif game['AwayTeam'] == team_a and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p2"  # Flyers win
                    else:
                        return "recommendation: p1"  # Rangers win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, unresolved
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or other status

    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Fallback in case of request failure

# Run the function and print the result
result = fetch_nhl_game_result()
print(result)