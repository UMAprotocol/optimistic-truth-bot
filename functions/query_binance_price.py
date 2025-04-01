import requests
import argparse
from datetime import datetime, timedelta, timezone
import pytz


def get_close_price_at_specific_time(
    date_str, hour=12, minute=0, timezone_str="US/Eastern"
):
    """
    Fetches the 1-minute candle close price for BTCUSDT on Binance
    at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 12)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Close price as float
    """
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    )
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    params = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60_000,  # plus 1 minute
    }

    response = requests.get("https://api.binance.com/api/v3/klines", params=params)
    data = response.json()

    if not data:
        raise Exception(f"No data returned for {date_str} {time_str} {timezone_str}")

    close_price = float(data[0][4])
    return close_price


def main():
    parser = argparse.ArgumentParser(
        description="Get BTC prices on specific dates and times"
    )
    parser.add_argument(
        "--date1", required=True, help="First date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--date2", required=False, help="Second date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--hour", type=int, default=12, help="Hour in 24-hour format (default: 12)"
    )
    parser.add_argument("--minute", type=int, default=0, help="Minute (default: 0)")
    parser.add_argument(
        "--timezone", default="US/Eastern", help="Timezone (default: US/Eastern)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (json or text)",
    )

    args = parser.parse_args()

    # Fetch prices
    price_1 = get_close_price_at_specific_time(
        args.date1, args.hour, args.minute, args.timezone
    )

    price_2 = None
    if args.date2:
        price_2 = get_close_price_at_specific_time(
            args.date2, args.hour, args.minute, args.timezone
        )

    # Output results
    time_str = f"{args.hour:02d}:{args.minute:02d}"

    if args.format == "json":
        import json

        result = {
            "date1": args.date1,
            "price1": price_1,
            "time": time_str,
            "timezone": args.timezone,
        }
        if args.date2:
            result["date2"] = args.date2
            result["price2"] = price_2
        print(json.dumps(result))
    else:
        print(f"BTC price on {args.date1}, {time_str} {args.timezone}: {price_1}")
        if args.date2:
            print(f"BTC price on {args.date2}, {time_str} {args.timezone}: {price_2}")


if __name__ == "__main__":
    main()

# Example usage:
# 1. Get price for a specific date at default time (12:00 PM ET):
#    python functions/query_binance_price.py --date1 2025-03-29
#
# 2. Get price for a specific date and time:
#    python functions/query_binance_price.py --date1 2025-03-29 --hour 15 --minute 30
#
# 3. Get prices for two dates at the same specified time:
#    python functions/query_binance_price.py --date1 2025-03-29 --date2 2025-03-30 --hour 9 --minute 30 --timezone "US/Pacific"
#
# 4. Get prices in JSON format:
#    python functions/query_binance_price.py --date1 2025-03-29 --date2 2025-03-30 --hour 14 --minute 0 --format json
