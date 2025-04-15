# Large Language Oracle (LLO)

A multi-agent system for resolving Polymarket prediction market proposals with high accuracy using large language models.

## Table of Contents

- [Large Language Oracle (LLO)](#large-language-oracle-llo)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [System Architecture](#system-architecture)
    - [Router](#router)
    - [Solvers](#solvers)
      - [Perplexity Solver](#perplexity-solver)
      - [Code Runner Solver](#code-runner-solver)
    - [Overseer](#overseer)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
  - [Running the System](#running-the-system)
    - [Proposal Fetcher](#proposal-fetcher)
    - [Multi-Operator Early Request Retry](#multi-operator-early-request-retry)
    - [Output Watcher](#output-watcher)
    - [Proposal Finalizer](#proposal-finalizer)
    - [User Interface](#user-interface)
  - [Development](#development)
  - [License](#license)

## Overview

The Large Language Oracle (LLO) is a sophisticated system designed to monitor, process, and resolve Polymarket prediction market proposals. The system combines multiple AI strategies, including search-based solvers and code execution solvers, to provide accurate resolution recommendations.****

The workflow involves:

1. Monitoring Polymarket blockchain events for new proposals
2. Saving proposal information to structured files
3. Processing proposals through multi-agent decision-making
4. Submitting resolution recommendations
5. Tracking performance against actual market outcomes

## System Architecture

The LLO system consists of several key components:

```mermaid
flowchart TD
    A[Blockchain Events] -->|ProposePrice events| B[Proposal Fetcher]
    B -->|Saves proposal data| C[Proposal File]
    C -->|Input| D[Multi-Operator System]
    D -->|Request routing| E[Router]
    
    E -->|Sports/Crypto queries| F[Code Runner Solver]
    E -->|General knowledge queries| G[Perplexity Solver]
    
    F -->|Resolution recommendations| H[Overseer]
    G -->|Resolution recommendations| H
    
    H -->|If satisfied: Final validation| I[Final Resolution]
    I -->|p1, p2, p3, p4| J[Result Output]
    
    J -->|Stored in| K[Results Files]
    K -->|Imported by| L[MongoDB/Database]
    
    M[Proposal Finalizer] -->|Updates results with actual outcomes| K
    L -->|Queried by| N[API & UI]
    
    H -->|If not satisfied: Request re-routing| E
    
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#bbf,stroke:#333,stroke-width:1px
    style F fill:#bbf,stroke:#333,stroke-width:1px
    style G fill:#bbf,stroke:#333,stroke-width:1px
    style H fill:#bbf,stroke:#333,stroke-width:1px
    
    classDef feedback stroke:#f00,stroke-width:2px,stroke-dasharray: 5 5
    class H-->E feedback
```

### Router

The Router is responsible for deciding which solver to use for each Polymarket proposal. It analyzes the content of the proposal and makes intelligent routing decisions based on the type of query and available solvers. The Router can select multiple solvers for complementary approaches to the same question.

### Solvers

The system currently employs two primary solver types:

#### Perplexity Solver

The Perplexity Solver leverages the Perplexity API to search the internet and retrieve information relevant to the proposal. It's engineered to handle a wide range of query types and includes validations to avoid hallucinations and maintain accuracy.

Key features:
- Web search capability
- Information synthesis from multiple sources
- Handling of complex queries requiring context

#### Code Runner Solver

The Code Runner Solver generates and executes Python code to solve specific types of proposals through direct API access. It's primarily used for:
- Cryptocurrency price queries (via Binance API)
- Sports data retrieval (via Sports Data IO API)

The Code Runner includes sample code templates that are adapted to each query, allowing for precise data retrieval and processing.

### Overseer

The Overseer evaluates solver responses for quality and accuracy. It can:
- Validate responses against market data
- Request reruns from solvers if needed
- Provide guidance for improving responses
- Make final recommendations on which solver's output to use

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB (for database storage)
- API keys:
  - OpenAI API key
  - Perplexity API key
  - Sports Data IO API key (for sports data)
  - Other optional API keys based on use cases

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/large-language-oracle.git
   cd large-language-oracle
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   SPORTS_DATA_IO_MLB_API_KEY=your_sports_data_io_mlb_api_key
   SPORTS_DATA_IO_NHL_API_KEY=your_sports_data_io_nhl_api_key
   POLYGON_RPC_URL=your_polygon_rpc_url
   MONGO_URI=your_mongodb_connection_string
   ```

2. Configure `api_keys_config.json` with additional API keys and endpoints needed for the Code Runner solver:

   The `api_keys_config.json` file provides structured configuration for data sources and API keys:
   
   ```json
   {
     "data_sources": [
       {
         "name": "Binance Cryptocurrency",
         "category": "crypto",
         "description": "Binance API for cryptocurrency price data",
         "api_keys": ["BINANCE_API_KEY"],
         "endpoints": {
           "primary": "https://api.binance.com/api/v3",
           "proxy": "https://your-proxy-endpoint.com/binance"
         },
         "example_queries": [
           "What was the price of BTC on March 30?",
           "How much did Ethereum cost yesterday?"
         ]
       },
       {
         "name": "Sports Data IO",
         "category": "sports",
         "subcategory": "MLB",
         "description": "Sports Data IO API for baseball statistics",
         "api_keys": ["SPORTS_DATA_IO_MLB_API_KEY"],
         "endpoints": {
           "primary": "https://api.sportsdata.io/v3/mlb"
         },
         "example_queries": [
           "Did the Blue Jays win against the Orioles?",
           "What was the score of the Yankees game?"
         ]
       },
       {
         "name": "Sports Data IO",
         "category": "sports",
         "subcategory": "NHL",
         "description": "Sports Data IO API for hockey statistics",
         "api_keys": ["SPORTS_DATA_IO_NHL_API_KEY"],
         "endpoints": {
           "primary": "https://api.sportsdata.io/v3/nhl"
         },
         "example_queries": [
           "Did the Kraken beat the Golden Knights?",
           "What was the score of the Maple Leafs vs Bruins game?"
         ]
       }
     ]
   }
   ```

   This configuration helps the Code Runner solver determine which APIs to use for different types of queries.

## Running the System

The system operates through several key scripts that work together to form a complete pipeline:

### Proposal Fetcher

The Proposal Fetcher listens for ProposePrice events on the blockchain, fetches on-chain data, and saves proposals to JSON files. It ignores negative risk markets.

```bash
python ./utilities/proposal_fetcher.py --start-block 70297560 --proposals-dir ./proposals/current-dataset/proposals
```

Parameters:
- `--start-block`: The block number to start listening from
- `--proposals-dir`: Directory to save proposal JSON files

### Multi-Operator Early Request Retry

This script processes proposals, determines the appropriate solver to use, and generates responses with recommendations.

```bash
./multi_operator/run_early_retry.py --output-dir ./results/current-run/outputs --proposals-dir ./proposals/current-dataset/proposals --check-interval 30
```

Parameters:
- `--output-dir`: Directory to save output JSON files
- `--proposals-dir`: Directory containing proposal JSON files to process
- `--check-interval`: Interval in seconds between checking for new proposals

### Output Watcher

The Output Watcher monitors the results directory for new files and automatically imports them into MongoDB.

```bash
python ./database_utilities/output_watcher.py --watch-dir ./results/current-run --database uma_oracle --collection experiments
```

Parameters:
- `--watch-dir`: Directory containing experiment results to watch
- `--database`: MongoDB database name
- `--collection`: MongoDB collection name

### Proposal Finalizer

The Proposal Finalizer checks unresolved proposals/outputs and updates them with final resolution prices from the blockchain.

```bash
python ./utilities/proposal_finalizer.py --continuous
```

Parameters:
- `--continuous`: Run in continuous mode, rechecking proposals periodically
- `--interval`: Interval in seconds between rechecks (default: 30)

### User Interface

The system includes a web-based UI for exploring results and monitoring the system.

```bash
python ./ui/server.py
```

Then open your browser to http://localhost:8000

## Development

The system is organized into several directories:

- `api/`: API for exposing results and system functionality
- `database_utilities/`: Tools for MongoDB integration
- `multi_operator/`: Core system components (router, solvers, overseer)
- `proposals/`: Storage for proposal data
- `results/`: Storage for system outputs
- `ui/`: Web-based user interface
- `utilities/`: Various utility scripts

## License

[MIT License](LICENSE)