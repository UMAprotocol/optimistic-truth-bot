# PolyMarket Oracle Agentic System

A minimal viable agentic system built with OpenAI's Agents SDK that recreates the multi-operator implementation for processing PolyMarket prediction market proposals.

## Overview

This system implements the same core architecture as the existing multi-operator system but using OpenAI's Agents framework:

1. **Router Agent**: Analyzes proposals and routes them to appropriate solver(s)
2. **Solver Agents**: Process proposals using different strategies
   - **Perplexity Solver**: Web search and general knowledge
   - **Code Runner Solver**: Precise data retrieval via APIs
3. **Overseer Agent**: Evaluates solver results and ensures quality

## Architecture

```
PolyMarket Proposal → Router Agent → Solver Agent(s) → Overseer Agent → Final Result
```

### Components

- **`router_agent.py`**: Routes questions to appropriate solvers based on query type
- **`perplexity_solver.py`**: Handles general knowledge and web search queries  
- **`code_runner_solver.py`**: Executes code to fetch precise data from APIs
- **`overseer_agent.py`**: Quality control and final evaluation
- **`manager.py`**: Orchestrates the entire flow
- **`main.py`**: CLI entry point

## Features

✅ **Compatible with existing proposal format**: Reads the same JSON proposal files  
✅ **Multi-agent routing**: Intelligently selects solvers based on query type  
✅ **Market price validation**: Considers current market sentiment in evaluation  
✅ **Parallel solver execution**: Can run multiple solvers simultaneously  
✅ **Quality oversight**: Comprehensive evaluation before final recommendation  
✅ **Result compatibility**: Outputs in format compatible with existing system  

## Installation & Setup

1. **Install dependencies** (assumes you're in the `open-ai-agentic` directory):
```bash
pip install openai-agents-sdk rich
```

2. **Set up environment variables**:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export PERPLEXITY_API_KEY="your-perplexity-api-key"  # if using Perplexity
```

3. **Configure API keys** (create `api_keys_config.json`):
```json
{
  "api_keys": {
    "BINANCE_API_KEY": "your-binance-key",
    "SPORTS_DATA_IO_MLB_API_KEY": "your-sports-key"
  }
}
```

## Usage

### Process a Single Proposal

```bash
python -m polymarket_oracle.main --single-proposal ../proposals/01042025-backtest-cherrypicked/proposals/questionId_e5373cc5.json --verbose
```

### Process Multiple Proposals

```bash
python -m polymarket_oracle.main \
  --proposals-dir ../proposals/01042025-backtest-cherrypicked/proposals \
  --output-dir ./output \
  --max-proposals 10 \
  --verbose
```

### Command Line Options

- `--proposals-dir`: Directory containing proposal JSON files
- `--output-dir`: Directory to save results  
- `--max-proposals`: Maximum number of proposals to process
- `--single-proposal`: Process a single proposal file
- `--verbose`: Enable detailed output

## Example Output

The system generates results in JSON format compatible with the existing system:

```json
{
  "query_id": "0xe5373cc5...",
  "recommendation": "p2",
  "proposal_metadata": { ... },
  "agentic_results": {
    "routing_decision": {
      "solvers": ["code_runner"],
      "reason": "Cryptocurrency price query with specific dates requires precise API data",
      "multi_solver_strategy": ""
    },
    "solver_results": {
      "code_runner": {
        "recommendation": "p2",
        "reasoning": "BTC price on March 16 was higher than March 15",
        "confidence": "High"
      }
    },
    "overseer_evaluation": {
      "verdict": "SATISFIED",
      "final_recommendation": "p2",
      "confidence_score": 0.85
    }
  }
}
```

## Agent Details

### Router Agent
- Analyzes query content and type
- Selects appropriate solver(s) based on:
  - Crypto price queries → Code Runner
  - Sports data → Code Runner  
  - General knowledge → Perplexity
  - Complex queries → Combined approach
- Returns routing decision with reasoning

### Solver Agents

**Perplexity Solver**:
- Uses web search for up-to-date information
- Good for current events, politics, general knowledge
- Returns recommendation with sources and reasoning

**Code Runner Solver**:
- Generates and executes Python code
- Accesses APIs for precise data (Binance, Sports Data IO)
- Handles timezone conversions and date parsing
- Returns recommendation with code and data

### Overseer Agent
- Evaluates solver results for accuracy
- Checks market alignment and reasoning quality
- Can request re-runs or default to p4 if needed
- Provides final quality-assured recommendation

## Integration with Existing System

This agentic system is designed to be a drop-in replacement for the existing multi-operator system:

1. **Input compatibility**: Reads the same proposal JSON files
2. **Output compatibility**: Generates results in the expected format
3. **API compatibility**: Can use the same API keys and data sources
4. **Workflow compatibility**: Follows the same routing → solving → oversight pattern

## Testing

Test with a sample proposal:

```bash
# Test with the Bitcoin price example
python -m polymarket_oracle.main \
  --single-proposal ../proposals/01042025-backtest-cherrypicked/proposals/questionId_e5373cc5.json \
  --verbose
```

Expected output:
- Router should select `code_runner` for the Bitcoin price query
- Code Runner should generate code to fetch Binance price data
- Overseer should validate the result and approve it
- Final recommendation should be based on actual price comparison

## Comparison with Multi-Operator System

| Feature | Multi-Operator | Agentic System |
|---------|----------------|----------------|
| **Architecture** | Class-based, procedural | Agent-based, declarative |
| **Routing** | ChatGPT + custom parsing | Router Agent with structured output |
| **Solvers** | Perplexity + Code Runner classes | Solver Agents with clear interfaces |
| **Oversight** | ChatGPT Overseer class | Overseer Agent with structured evaluation |
| **Error Handling** | Try/catch with fallbacks | Agent-level error handling |
| **Extensibility** | Add new solver classes | Add new agent definitions |
| **Tracing** | Custom logging | Built-in OpenAI tracing |
| **Testing** | Manual testing scripts | Agent unit testing capabilities |

## Future Enhancements

- **New Solver Agents**: Add agents for different data sources
- **Enhanced Router**: More sophisticated routing logic
- **Batch Processing**: Process multiple proposals in parallel
- **Real-time Processing**: Monitor proposal directories for new files
- **API Integration**: Direct integration with PolyMarket APIs
- **Performance Monitoring**: Track agent performance and optimization

## Troubleshooting

**Common Issues**:

1. **Missing API keys**: Ensure `OPENAI_API_KEY` is set
2. **Module import errors**: Run from the correct directory
3. **JSON parsing errors**: Verify proposal file format
4. **Agent timeouts**: Check network connectivity

**Debug Tips**:
- Use `--verbose` flag for detailed output
- Check OpenAI traces for agent execution details
- Validate proposal JSON structure
- Test with known working proposals first