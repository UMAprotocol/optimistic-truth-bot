# Query Utilities

This directory contains scripts for fetching market data from the blockchain.

## Files

- `fetch_market_resolution.py`: Fetches the market resolution for a given market ID.
- `fetch_open_market_Ids.py`: Fetches all open markets from a defined block number and stores them in a specified output file.

## How to Run

### Fetching Market Resolution

```bash
# Fetch market resolution for a specific market ID
python query_utilities/fetch_market_resolution.py 0x0FC5D2B61B29D54D487ACBC27E9694CEF303A9891433925E282742B1DBA4F399
```

### Fetching Open Market IDs

```bash
# Fetch all open markets from block 68853567 and save to output_file.json
python query_utilities/fetch_open_market_Ids.py 68853567 output_file.json
```

This command will:
1. Connect to the Polygon blockchain
2. Retrieve all market questions initialized since the specified block
3. Store the market data in the specified output file 