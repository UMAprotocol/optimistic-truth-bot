# Proposal Replayer

This directory contains scripts for monitoring and processing UMA Optimistic Oracle proposals.

## Files

- `proposal_fetcher.py`: Monitors the blockchain for new proposals to the Optimistic Oracle. When it detects a proposal, it fetches the associated on-chain information and saves it in the `proposals` directory.
- `proposal_replayer.py`: Listens for new files added to the `proposals` directory. For each proposal file, it queries the Perplexity API to find the associated solution and saves the result to the `outputs` directory.

## How to Run

### Proposal Fetcher

To monitor for new proposals starting from a specific block:

```bash
# Start monitoring from block 68945138
python proposal_replayer/proposal_fetcher.py --start-block 68945138
```

### Proposal Replayer

To process proposals and query the Perplexity API:

```bash
# Process proposal files and query the API
python proposal_replayer/proposal_replayer.py
```

This will:
1. Check for any existing unprocessed proposals in the `proposals` directory
2. Process them by querying the Perplexity API
3. Save the results in the `outputs` directory
4. Continue monitoring for new proposal files

Note: Make sure your `.env` file contains the `PERPLEXITY_API_KEY` variable. 