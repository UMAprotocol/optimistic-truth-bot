import os
import requests
from dotenv import load_dotenv

def fetch_nhl_game_result():
    # Load environment variables
    load_dotenv()
    
    # Retrieve API key from environment variable
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    
    # Define the API endpoint
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-10"
    
    # Set up headers with the API key
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response
        games = response.json()
        
        # Define the teams involved in the query
        team_a = "Detroit Red Wings"
        team_b = "Florida Panthers"
        
        # Search for the specific game
        for game in games:
            if team_a in game['HomeTeam'] and team_b in game['AwayTeam'] or team_a in game['AwayTeam'] and team_b in game['HomeTeam']:
                if game['Status'] == "Final":
                    # Determine the winner
                    if game['HomeTeam'] == team_a and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"  # Red Wings win
                    elif game['AwayTeam'] == team_a and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p2"  # Red Wings win
                    else:
                        return "recommendation: p1"  # Panthers win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, market remains open
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or future game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p3"  # Unknown error, resolve 50-50

# Run the function and print the result
result = fetch_nhl_game_result()
print(result)