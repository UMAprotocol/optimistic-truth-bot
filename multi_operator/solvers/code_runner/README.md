# Code Runner Solver

The Code Runner solver generates and executes Python code using ChatGPT to solve prediction market questions, particularly those that require accessing external APIs for data.

## Supported Data Sources

Currently, the Code Runner is optimized for:

1. **Cryptocurrency Data**: Fetches price data from Binance API (no API key required)
2. **Sports Data**: Fetches MLB game data using Sports Data IO API
3. **Additional Sports Data**: Can fetch NFL, NBA, and other sports data when proper API keys are configured

## API Key Configuration

The Code Runner now supports configuring multiple API keys, which allows the generated code to access a wider range of data sources. API keys can be provided in three ways:

1. **Environment Variables**: Standard method, keys defined in the environment or .env file
2. **Configuration File**: JSON or .env-style file with API keys
3. **Direct Parameters**: API keys passed directly when initializing the CodeRunnerSolver

### API Key Naming Conventions

For automatic recognition of API purposes, follow these naming conventions:

- Sports Data IO API keys: `SPORTS_DATA_IO_[LEAGUE]_API_KEY`
  - Examples: `SPORTS_DATA_IO_MLB_API_KEY`, `SPORTS_DATA_IO_NFL_API_KEY`, `SPORTS_DATA_IO_NBA_API_KEY`
- Other APIs: Use descriptive names like `WEATHER_API_KEY`, `NEWS_API_KEY`, etc.

### Configuration File Format

You can create configuration files in JSON or .env format:

**JSON format (api_keys.json)**:
```json
{
  "api_keys": {
    "SPORTS_DATA_IO_MLB_API_KEY": "your-mlb-api-key",
    "SPORTS_DATA_IO_NBA_API_KEY": "your-nba-api-key",
    "SPORTS_DATA_IO_NFL_API_KEY": "your-nfl-api-key",
    "WEATHER_API_KEY": "your-weather-api-key"
  }
}
```

**OR .env-style format (api_keys.env)**:
```
SPORTS_DATA_IO_MLB_API_KEY=your-mlb-api-key
SPORTS_DATA_IO_NBA_API_KEY=your-nba-api-key
SPORTS_DATA_IO_NFL_API_KEY=your-nfl-api-key
WEATHER_API_KEY=your-weather-api-key
```

### Using in Code

When initializing the CodeRunnerSolver, you can provide API keys:

```python
# Using a configuration file
solver = CodeRunnerSolver(
    api_key=openai_api_key,
    verbose=True,
    config_file="path/to/api_keys.json"
)

# OR directly passing API keys
solver = CodeRunnerSolver(
    api_key=openai_api_key,
    verbose=True,
    additional_api_keys={
        "SPORTS_DATA_IO_NFL_API_KEY": "your-nfl-api-key",
        "WEATHER_API_KEY": "your-weather-api-key"
    }
)
```

## How It Works

1. The Code Runner analyzes the input query to determine what type of data it needs to fetch
2. It generates Python code specifically tailored to solve that query
3. The code is executed in a controlled environment
4. The output is analyzed to extract a recommendation (p1, p2, p3, or p4)

## Sample Functions

The `sample_functions` directory contains templates that serve as examples for the code generator:

- `query_binance_price.py`: Template for cryptocurrency price queries
- `query_sports_mlb_data.py`: Template for MLB sports data queries
- `query_sports_nfl_data.py`: Template for NFL sports data queries

## Adding Support for New Data Sources

To add support for new data sources:

1. Create a new sample function in the `sample_functions` directory
2. Update the API key configuration with appropriate naming
3. Add detection logic for the new query type in the `determine_query_type` method

## Limitations

- The generated code is only as good as the instructions provided
- API rate limits may affect the ability to fetch data
- Some data sources may require paid API access

## Purpose

The Code Runner solver enables the system to:

1. Generate Python code based on the prediction market question using ChatGPT
2. Execute the generated code on the server to fetch real-time data
3. Parse the output to determine the appropriate recommendation (p1, p2, p3, or p4)

The primary use cases are questions that require current data from APIs such as:
- Cryptocurrency prices from Binance
- MLB sports data from Sports Data IO

## Directory Structure

- `code_runner_solver.py`: Main implementation of the CodeRunnerSolver
- `__init__.py`: Module initialization
- `sample_functions/`: Directory containing template functions for different query types
  - `query_binance_price.py`: Template for cryptocurrency price queries
  - `query_sports_mlb_data.py`: Template for MLB sports data queries
- `executed_functions/`: Directory where generated code files are saved and executed

## Usage

The Code Runner solver is integrated into the Multi-Operator system and can be selected by the router component based on the query type.

When the router selects the Code Runner, it will:

1. Generate code to fetch the necessary data
2. Execute the code
3. Process the output to determine a recommendation
4. Pass the result to the overseer for evaluation

## Example Generated Code

Generated code is saved with a timestamp and query type identifier:
```
crypto_20230401_120000.py
sports_mlb_20230401_123045.py
```

## Security Considerations

Since this solver executes code on the server, it has important security implications:

1. The code is generated in a sandboxed environment
2. Execution is limited to specific types of queries (crypto and MLB data)
3. A timeout is enforced to prevent long-running processes
4. No direct file system access beyond the necessary API calls

## Extension

To add support for more data sources:

1. Add a new sample function in the `sample_functions` directory
2. Update the `determine_query_type` method in `code_runner_solver.py`
3. Update the router to be aware of the new capability 