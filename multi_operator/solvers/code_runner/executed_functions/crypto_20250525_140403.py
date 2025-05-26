import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

def fetch_hyperliquid_data(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 'Close' price for the HYPE/USDC pair from Hyperliquid at a specific time.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 12)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Close price as float or None if data cannot be fetched
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    timestamp = int(target_time_utc.timestamp() * 1000)  # Convert to milliseconds

    # Hyperliquid API endpoint
    url = "https://app.hyperliquid.xyz/trade/HYPE/USDC"
    params = {
        "interval": "1m",
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and 'close' in data:
            return float(data['close'])
        else:
            return None
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def resolve_market():
    """
    Resolves the market based on the 'Close' prices from Hyperliquid for the specified dates and times.
    """
    price_may_23 = fetch_hyperliquid_data("2025-05-23")
    price_may_24 = fetch_hyperliquid_data("2025-05-24")

    if price_may_23 is None or price_may_24 is None:
        print("recommendation: p4")  # Unable to fetch data
    elif price_may_23 < price_may_24:
        print("recommendation: p2")  # Up
    elif price_may_23 > price_may_24:
        print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # 50-50

if __name__ == "__main__":
    resolve_market()