# Large Language Oracle for UMA Protocol

A system for using large language models to resolve Optimistic Oracle proposals in the UMA protocol.

## Repository Structure

- **example/**: Contains example code showing simple Perplexity API usage
  - `example.py`: Basic implementation of Perplexity API queries with sample data
  - See [example/README.md](example/README.md) for more details

- **query_utilities/**: Tools for fetching market data from the blockchain
  - `fetch_market_resolution.py`: Fetches resolution data for a specific market ID
  - `fetch_open_market_Ids.py`: Retrieves all open markets from a specified block
  - See [query_utilities/README.md](query_utilities/README.md) for more details

- **proposal_replayer/**: Core system for monitoring and processing UMA proposals
  - `proposal_fetcher.py`: Monitors the blockchain for new proposals and saves them
  - `proposal_replayer.py`: Processes saved proposals with the Perplexity API
  - See [proposal_replayer/README.md](proposal_replayer/README.md) for more details

- **api/**: API for querying Oracle outputs from MongoDB
  - `main.py`: FastAPI application with endpoints for querying Oracle outputs
  - `test_api.py`: Test script for API functionality
  - See [api/README.md](api/README.md) for more details

- **database_utilities/**: Tools for MongoDB integration
  - `output_watcher.py`: Watches for new output files and adds them to MongoDB
  - `results_to_mongodb.py`: Imports result files to MongoDB
  - See [database_utilities/README.md](database_utilities/README.md) for more details

- **Common Files**:
  - `common.py`: Shared utilities and constants
  - `prompt.py`: Prompt creation and formatting for API calls

## Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (or create a .env file)
export PERPLEXITY_API_KEY=<your_perplexity_api_key>
export POLYGON_RPC_URL=<your_polygon_rpc_url>
```

## Running the Proposal Replayer System

1. Start the proposal fetcher to monitor for new proposals:
```bash
python proposal_replayer/proposal_fetcher.py --start-block 68945138
```

2. In a separate terminal, start the proposal replayer:
```bash
python proposal_replayer/proposal_replayer.py
```

## Running the API Server

To start the API server for querying Oracle outputs from MongoDB:

```bash
cd api
./run_api.sh
```

The API will be available at http://localhost:8000. See [api/README.md](api/README.md) for detailed endpoint documentation.

## Utility Commands

### Fetching Market Resolution
```bash
python query_utilities/fetch_market_resolution.py 0x0FC5D2B61B29D54D487ACBC27E9694CEF303A9891433925E282742B1DBA4F399
```