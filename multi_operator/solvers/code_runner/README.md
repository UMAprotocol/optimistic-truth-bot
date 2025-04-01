# Code Runner Solver

The Code Runner solver is a component of the UMA Multi-Operator System that can execute arbitrary code to fetch specific data needed to resolve prediction market questions.

## Purpose

The Code Runner solver enables the system to:

1. Generate Python code based on the prediction market question using ChatGPT
2. Execute the generated code on the server to fetch real-time data
3. Parse the output to determine the appropriate recommendation (p1, p2, p3, or p4)

The primary use cases are questions that require current data from APIs such as:
- Cryptocurrency prices from Binance
- MLB sports data from Sports Data IO

## How It Works

1. **Query Analysis**: The solver first determines what type of data is needed based on the prediction market question.

2. **Code Generation**: Using OpenAI's GPT models, the solver generates Python code to fetch and analyze the necessary data. It uses sample functions as templates when appropriate.

3. **Code Execution**: The generated code is saved to a file in the `executed_functions` directory and executed on the server.

4. **Output Processing**: The output from the executed code is parsed to extract a recommendation (p1, p2, p3, or p4).

5. **Retry Mechanism**: If code execution fails, the solver can regenerate and retry up to a configurable number of times.

## Directory Structure

- `code_runner_solver.py`: Main implementation of the CodeRunnerSolver
- `__init__.py`: Module initialization
- `sample_functions/`: Directory containing template functions for different query types
  - `query_binance_price.py`: Template for cryptocurrency price queries
  - `query_sports_mlb_data.py`: Template for MLB sports data queries
- `executed_functions/`: Directory where generated code files are saved and executed

## API Keys Required

- For Binance queries: No API key required for public endpoints
- For Sports Data IO: `SPORTS_DATA_IO_MLB_API_KEY` should be set in the environment or in a `.env` file

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