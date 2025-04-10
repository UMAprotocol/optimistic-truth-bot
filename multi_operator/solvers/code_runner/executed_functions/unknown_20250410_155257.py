import os
import requests
from dotenv import load_dotenv

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
        print(f"Error fetching or processing data: {e}")
        return None

def process_temperature_data(data):
    # Split the data into lines
    lines = data.splitlines()
    march_temperatures = {}

    # Extract year and March temperature
    for line in lines:
        if line.startswith("Year"):
            continue  # Skip the header line
        parts = line.split()
        if len(parts) >= 4:  # Ensure there are enough columns
            year = parts[0]
            march_temp = parts[3]  # March is the fourth column (index 3)
            if march_temp != "****":  # Ensure the data is not missing
                march_temperatures[year] = float(march_temp)

    return march_temperatures

def determine_resolution(march_temperatures):
    # Find the maximum temperature recorded in March before 2025
    max_temp = max(value for key, value in march_temperatures.items() if key != "2025" and key.isdigit())

    # Compare with March 2025 temperature
    march_2025_temp = march_temperatures.get("2025")
    if march_2025_temp is None:
        return "recommendation: p3"  # Unknown if no data for 2025
    elif march_2025_temp > max_temp:
        return "recommendation: p2"  # Yes, 2025 is the hottest
    else:
        return "recommendation: p1"  # No, 2025 is not the hottest

def main():
    march_temperatures = fetch_temperature_data()
    if march_temperatures is not None:
        result = determine_resolution(march_temperatures)
        print(result)
    else:
        print("recommendation: p3")  # Unknown due to data fetch failure

if __name__ == "__main__":
    main()