# Proposal Replayer

This directory contains scripts for monitoring and processing UMA Optimistic Oracle proposals.

## Files

- `proposal_fetcher.py`: Monitors the blockchain for new proposals to the Optimistic Oracle. When it detects a proposal, it fetches the associated on-chain information and saves it in the `proposals` directory.
- `proposal_replayer.py`: Listens for new files added to the `proposals` directory. For each proposal file, it queries the Perplexity API to find the associated solution and saves the result to the `outputs` directory.
- `ui/`: Web interface for visualizing proposal outputs and reruns.

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

### Visualization UI

To view and explore the outputs and reruns:

```bash
# Navigate to the UI directory
cd proposal_replayer/ui

# Run the UI server
python server.py
```

This will start a local web server and open your browser to the visualization interface. The UI allows you to:

- Browse all outputs and reruns
- Search and filter results
- View detailed information for each proposal

For more details, see the [UI README](ui/README.md). 