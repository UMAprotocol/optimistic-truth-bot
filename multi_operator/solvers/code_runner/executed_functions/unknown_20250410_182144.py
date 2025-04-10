import requests
import os
from dotenv import load_dotenv

def fetch_temperature_data():
    # Load environment variables
    load_dotenv()

    # Define the URL for the NASA Global Temperature data
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt"

    try:
        # Fetch the data
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Process the data
        return process_temperature_data(response.text)
    except requests.RequestException as e:
        return {"error": str(e)}

def process_temperature_data(data):
    # Split the data into lines
    lines = data.splitlines()
    march_temperatures = {}

    # Extract temperature data for March from the relevant column
    for line in lines:
        if line.startswith("Year") or line.startswith("Yearly"):
            continue
        parts = line.split()
        if len(parts) >= 4:  # Ensure there are enough columns
            year = parts[0]
            march_temp = parts[3]  # March is the 4th column (index 3)
            if march_temp != "****":  # Ignore placeholder data
                march_temperatures[year] = float(march_temp)

    # Determine if March 2025 has the highest temperature on record
    march_2025_temp = march_temperatures.get("2025")
    if march_2025_temp is None:
        return {"result": "Data for March 2025 is not available", "recommendation": "p3"}

    # Check if 2025 is the hottest March on record
    hottest = all(march_2025_temp > temp for year, temp in march_temperatures.items() if year != "2025")
    
    if hottest:
        return {"result": "Yes, March 2025 is the hottest on record", "recommendation": "p2"}
    else:
        return {"result": "No, March 2025 is not the hottest on record", "recommendation": "p1"}

if __name__ == "__main__":
    result = fetch_temperature_data()
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(result["result"])
        print(f"recommendation: {result['recommendation']}")