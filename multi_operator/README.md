# UMA Multi-Operator System

A modular system for processing UMA optimistic oracle requests using multiple AI solvers.

## Overview

The UMA Multi-Operator System extends the existing proposal processing infrastructure by introducing a router component that decides which AI solver to use for a given proposal. Currently, the system supports Perplexity as its primary solver, but the architecture allows for easy integration of additional solvers in the future.

## Components

The system consists of the following key components:

1. **Router**: Analyzes the proposal and decides which solver to use
2. **Solvers**: Process proposals and generate recommendations
   - PerplexitySolver: Uses the Perplexity API to solve proposals
3. **Overseer**: Evaluates solver responses for accuracy and completeness
4. **Proposal Processor**: Monitors for new proposals and orchestrates the processing flow

## Directory Structure

```
multi-operator/
  ├── __init__.py
  ├── common.py                # Common utilities
  ├── proposal_processor.py    # Main processor
  ├── run_processor.py         # Command-line runner
  ├── router/
  │   ├── __init__.py
  │   └── router.py            # Router implementation
  ├── solvers/
  │   ├── __init__.py
  │   ├── base_solver.py       # Base solver interface
  │   └── perplexity_solver.py # Perplexity solver implementation
  └── overseer/
      ├── __init__.py
      ├── overseer.py          # Overseer implementation
      └── prompt_overseer.py   # Overseer prompt utilities
```

## Repository Structure

- **solvers/**: Contains implementations of different solvers
  - `base_solver.py`: Abstract base class for all solvers
  - `perplexity_solver.py`: Implementation of the Perplexity solver
  - **code_runner/**: Code Runner solver for executing arbitrary code
    - `code_runner_solver.py`: Implementation of the Code Runner solver
    - `sample_functions/`: Template functions for different query types
    - `executed_functions/`: Directory where generated code is saved and executed
    - See [code_runner/README.md](solvers/code_runner/README.md) for more details

- **router/**: Router component that decides which solver(s) to use
  - `router.py`: Implementation of the router

- **overseer/**: Overseer component that evaluates solver responses
  - `overseer.py`: Implementation of the overseer
  - `prompt_overseer.py`: Prompt templates for the overseer

- **Common Files**:
  - `common.py`: Shared utilities and constants
  - `proposal_processor.py`: Main processor for handling proposals

## Usage

### Prerequisites

Ensure you have the required API keys in your `.env` file:

```
PERPLEXITY_API_KEY=your_perplexity_api_key
OPENAI_API_KEY=your_openai_api_key
```

### Running the Processor

To run the processor with default settings:

```bash
python multi-operator/run_processor.py
```

Command-line options:

```
--proposals-dir PATH   Directory containing proposal JSON files (default: "proposals")
--output-dir PATH      Directory to store output files
--max-attempts N       Maximum number of attempts to process a proposal (default: 3)
--min-attempts N       Minimum number of attempts before defaulting to p4 (default: 2)
--start-block N        Block number to start processing from (default: 0)
--poll-interval N      Interval in seconds to poll for new proposals (default: 30)
--verbose              Enable verbose output with detailed logs
```

Example with custom settings:

```bash
python multi-operator/run_processor.py \
  --proposals-dir my_proposals \
  --output-dir results \
  --max-attempts 5 \
  --min-attempts 2 \
  --poll-interval 60 \
  --verbose
```

## Adding New Solvers

To add a new solver:

1. Create a new solver class in the `solvers` directory that inherits from `BaseSolver`
2. Implement the required methods (`solve()` and `get_name()`)
3. Register the solver in the `initialize_components()` method of `MultiOperatorProcessor`
4. Update the `Router` class to include the new solver in its decision-making

## Workflow

The system follows this workflow for each proposal:

1. **Monitoring**: Continuously monitors the proposals directory for new JSON files
2. **Routing**: Uses ChatGPT to decide which solver to use based on the proposal content
3. **Solving**: Passes the proposal to the selected solver
4. **Evaluation**: Evaluates the solver's response using the overseer
5. **Refinement**: If needed, retries with updated instructions
6. **Resolution**: Finalizes the recommendation (p1, p2, p3, p4) and saves the result 

## Solvers

The system includes multiple solvers that can be selected by the router based on the query type:

1. **Perplexity Solver**: Uses the Perplexity API to find information online to answer general questions.
   - **Capabilities**:
     - Searches online for up-to-date information
     - Handles complex, nuanced questions requiring general knowledge
     - Can interpret and explain concepts, events, and outcomes
     - Provides context and background information
   - **Limitations**:
     - May not have access to very recent information (knowledge cutoff)
     - Cannot access or process real-time data from specific APIs
     - Limited by the quality of information available online

2. **Code Runner Solver**: Executes custom code to fetch specific data from APIs.
   - **Capabilities**:
     - Fetches precise, real-time data from supported APIs
     - Currently supports:
       * Binance API: Cryptocurrency prices at specific times/dates
       * Sports Data IO: MLB game results, scores, and performance data
     - Can handle timezone conversions and date-specific queries
     - Provides deterministic results based on data sources
   - **Limitations**:
     - Only works with specifically supported data sources (Binance, MLB)
     - Cannot answer general knowledge questions
     - No contextual understanding beyond the data it fetches
     - Limited to the functionality implemented in the sample functions

The router can select one or multiple solvers for a given query. When multiple solvers are used, their results are combined and evaluated by the overseer to produce a final recommendation. This approach allows the system to leverage both precise data fetching and contextual understanding when needed.

**Example Multi-Solver Workflow**:
1. For a question like "Did BTC price rise after the SEC announcement on March 15th?"
2. The router selects both solvers
3. Code Runner fetches the precise BTC prices before and after March 15th
4. Perplexity provides context about the SEC announcement
5. The overseer combines these insights to determine the final recommendation 