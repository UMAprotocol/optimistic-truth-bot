import requests
import re
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Note: Binance public API doesn't require an API key for basic price queries
# However, if we need rate limits increased or private endpoints, we would use these:
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Sensitive data patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"BINANCE_API_KEY\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"BINANCE_API_SECRET\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"api_key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"api_secret\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"secret\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    # Add more patterns as needed
]

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        original_msg = record.getMessage()
        masked_msg = original_msg
        for pattern in SENSITIVE_PATTERNS:
            masked_msg = pattern.sub("******", masked_msg)
        record.msg = masked_msg
        return True

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

console_handler.addFilter(SensitiveDataFilter())

logger.addHandler(console_handler)


def get_close_price_at_specific_time(
    date_str, hour=12, minute=0, timezone_str="US/Eastern", symbol="BTCUSDT"
):
    """
    Fetches the 1-minute candle close price for a cryptocurrency pair on Binance
    at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 12)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")
        symbol: Trading pair symbol (default: "BTCUSDT")

    Returns:
        Close price as float
    """
    logger.info(f"Fetching {symbol} price for {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    try:
        tz = pytz.timezone(timezone_str)
        time_str = f"{hour:02d}:{minute:02d}:00"
        target_time_local = tz.localize(
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        )
        target_time_utc = target_time_local.astimezone(timezone.utc)
        start_time_ms = int(target_time_utc.timestamp() * 1000)
        
        logger.debug(f"Converted local time to UTC timestamp: {start_time_ms}")
    except Exception as e:
        logger.error(f"Error converting time: {e}")
        raise

    # First try the standard API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    logger.debug(f"Using primary Binance API endpoint: {api_url}")
    
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60_000,  # plus 1 minute
    }

    try:
        logger.debug(f"Requesting data with params: {params}")
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data:
            close_price = float(data[0][4])
            logger.info(f"Successfully retrieved price: {close_price}")
            return close_price
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"Primary API request failed: {e}")
        logger.info("Attempting to use backup API proxy...")
    except (IndexError, ValueError) as e:
        logger.warning(f"Error processing primary API response: {e}")
        logger.info("Attempting to use backup API proxy...")
    
    # Try backup proxy if primary fails
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    try:
        logger.debug(f"Using backup proxy API endpoint: {proxy_url}")
        proxy_response = requests.get(proxy_url, params=params)
        proxy_response.raise_for_status()
        proxy_data = proxy_response.json()
        
        if proxy_data:
            close_price = float(proxy_data[0][4])
            logger.info(f"Successfully retrieved price from proxy: {close_price}")
            return close_price
        
        logger.error(f"No data returned from either endpoint for {date_str} {time_str} {timezone_str}")
        raise Exception(f"No data available for {symbol} at {date_str} {time_str} {timezone_str}")
        
    except Exception as e:
        logger.error(f"All API requests failed: {e}")
        raise Exception(f"Failed to fetch {symbol} price data: {e}")


def extract_price_info_from_query(query_text):
    """
    Extract date, time, timezone, and symbol information from a query.
    This is a helper function to parse user queries for cryptocurrency prices.
    
    Args:
        query_text: The query text to analyze
        
    Returns:
        Dictionary with extracted information
    """
    import re
    
    # Default values
    info = {
        "date": "2025-03-30",  # Default date
        "hour": 12,            # Default hour (12 PM)
        "minute": 0,           # Default minute
        "timezone": "US/Eastern",  # Default timezone
        "symbol": "BTCUSDT",   # Default symbol
    }
    
    # Extract date (YYYY-MM-DD format)
    date_pattern = r"(\d{4}-\d{2}-\d{2})"
    date_match = re.search(date_pattern, query_text)
    if date_match:
        info["date"] = date_match.group(1)
        logger.debug(f"Extracted date: {info['date']}")
    
    # Extract time (HH:MM format or H:MM format)
    time_pattern = r"(\d{1,2}):(\d{2})"
    time_match = re.search(time_pattern, query_text)
    if time_match:
        info["hour"] = int(time_match.group(1))
        info["minute"] = int(time_match.group(2))
        logger.debug(f"Extracted time: {info['hour']}:{info['minute']}")
    
    # Extract AM/PM time references
    am_pm_pattern = r"(\d{1,2})\s*(am|pm)"
    am_pm_match = re.search(am_pm_pattern, query_text, re.IGNORECASE)
    if am_pm_match:
        hour = int(am_pm_match.group(1))
        period = am_pm_match.group(2).lower()
        
        # Convert to 24-hour format
        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
            
        info["hour"] = hour
        logger.debug(f"Extracted AM/PM time: {info['hour']}:00")
    
    # Extract timezone
    timezone_pattern = r"(ET|EST|EDT|PT|PST|PDT|CT|CST|CDT|MT|MST|MDT|UTC|GMT)"
    timezone_match = re.search(timezone_pattern, query_text, re.IGNORECASE)
    if timezone_match:
        tz_abbr = timezone_match.group(1).upper()
        # Map abbreviations to pytz timezone strings
        tz_map = {
            "ET": "US/Eastern",
            "EST": "US/Eastern",
            "EDT": "US/Eastern",
            "PT": "US/Pacific",
            "PST": "US/Pacific",
            "PDT": "US/Pacific",
            "CT": "US/Central",
            "CST": "US/Central",
            "CDT": "US/Central",
            "MT": "US/Mountain",
            "MST": "US/Mountain",
            "MDT": "US/Mountain",
            "UTC": "UTC",
            "GMT": "UTC",
        }
        if tz_abbr in tz_map:
            info["timezone"] = tz_map[tz_abbr]
            logger.debug(f"Extracted timezone: {info['timezone']}")
    
    # Extract cryptocurrency symbol
    # First check for common crypto abbreviations
    crypto_pattern = r"\b(BTC|ETH|XRP|BCH|LTC|ADA|DOT|LINK|XLM|DOGE|SOL)\b"
    crypto_match = re.search(crypto_pattern, query_text, re.IGNORECASE)
    if crypto_match:
        crypto = crypto_match.group(1).upper()
        info["symbol"] = f"{crypto}USDT"
        logger.debug(f"Extracted crypto symbol: {info['symbol']}")
    
    # Check for full cryptocurrency names
    crypto_names = {
        "bitcoin": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "ripple": "XRPUSDT",
        "bitcoin cash": "BCHUSDT",
        "litecoin": "LTCUSDT",
        "cardano": "ADAUSDT",
        "polkadot": "DOTUSDT",
        "chainlink": "LINKUSDT",
        "stellar": "XLMUSDT",
        "dogecoin": "DOGEUSDT",
        "solana": "SOLUSDT",
    }
    
    for name, symbol in crypto_names.items():
        if name.lower() in query_text.lower():
            info["symbol"] = symbol
            logger.debug(f"Extracted crypto name: {name} → {info['symbol']}")
            break
    
    return info

def determine_resolution(price1, price2=None, threshold=0.0):
    """
    Determine the resolution based on price comparison.
    
    Args:
        price1: First price point
        price2: Second price point (optional)
        threshold: Price difference threshold (optional)
        
    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    # If we only have one price, can't make a determination
    if price2 is None:
        return "p4"  # Too early to resolve
    
    # Calculate price difference in percentage
    price_diff = 100 * (price2 - price1) / price1
    
    if abs(price_diff) <= threshold:
        # Prices are within threshold, consider it neutral
        logger.info(f"Prices within threshold ({threshold}%): {price1} vs {price2}")
        return "p3"  # Neutral outcome
    elif price2 > price1:
        # Price increased
        logger.info(f"Price increased by {price_diff:.2f}%: {price1} → {price2}")
        return "p1"  # Positive outcome
    else:
        # Price decreased
        logger.info(f"Price decreased by {price_diff:.2f}%: {price1} → {price2}")
        return "p2"  # Negative outcome

def main():
    """
    Main function to handle cryptocurrency price queries.
    In a production environment, this function would parse the query to extract
    relevant information about which cryptocurrency, date, time, etc. to check.
    
    For this sample, we'll hardcode a common query pattern.
    """
    # This would normally be extracted from the user's query
    query = "What was the price of Bitcoin on March 30, 2025 at 12:00 PM ET compared to April 1, 2025 at the same time?"
    
    logger.info(f"Processing query: {query}")
    
    try:
        # Extract information from query
        info = extract_price_info_from_query(query)
        
        # For this example, we'll compare two dates
        date1 = "2025-03-30"  # First date
        date2 = "2025-04-01"  # Second date
        
        # Get prices for both dates
        price1 = get_close_price_at_specific_time(
            date1, info["hour"], info["minute"], info["timezone"], info["symbol"]
        )
        
        price2 = get_close_price_at_specific_time(
            date2, info["hour"], info["minute"], info["timezone"], info["symbol"]
        )
        
        # Log the results
        logger.info(f"Price on {date1}: {price1}")
        logger.info(f"Price on {date2}: {price2}")
        
        # Determine if price went up (p1), down (p2), or was neutral (p3)
        # This is just an example - actual resolution mapping would depend on the specific question
        resolution = determine_resolution(price1, price2)
        
        # Output the recommendation
        print(f"recommendation: {resolution}")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        # Default to p4 (too early to resolve) in case of any errors
        print("recommendation: p4")


if __name__ == "__main__":
    main()
