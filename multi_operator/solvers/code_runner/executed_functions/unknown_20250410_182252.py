import requests
from dotenv import load_dotenv
import os
import datetime

def fetch_temperature_data():
    # Load environment variables
    load_dotenv()

    # Define the URL for the NASA Global Temperature data
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt"

    try:
        # Fetch the data
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses

        # Process the data
        return process_temperature_data(response.text)
    except requests.RequestException as e:
        return {"error": str(e)}

def process_temperature_data(data):
    # Split the data into lines
    lines = data.splitlines()
    march_temperatures = {}
    current_year = datetime.datetime.now().year

    # Extract temperature data for March
    for line in lines:
        if line.startswith("Year") or len(line) < 5:
            continue
        parts = line.split()
        year = int(parts[0])
        if year > current_year:
            continue
        # March data is the third month, index 2
        try:
            march_temp = float(parts[2])
            march_temperatures[year] = march_temp
        except ValueError:
            continue  # Skip years with missing data

    # Check if March 2025 has the highest temperature
    march_2025_temp = march_temperatures.get(2025, None)
    if march_2025_temp is None:
        return {"recommendation": "p3"}  # Unknown if data for 2025 is not available

    # Determine if 2025 is the hottest on record
    hottest = all(march_2025_temp > temp for year, temp in march_temperatures.items() if year != 2025)
    return {"recommendation": "p2" if hottest else "p1"}

if __name__ == "__main__":
    result = fetch_temperature_data()
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"recommendation: {result['recommendation']}")