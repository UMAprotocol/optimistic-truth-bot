# Example Scripts

This directory contains example scripts for interacting with the Perplexity API.

## Files

- `example.py`: Shows the simplest possible Perplexity query and generates a file in the results directory that contains the model output.
- `sample_OO_queries.py`: Contains sample Optimistic Oracle queries used for testing.

## How to Run

### Running example.py

```bash
# Make sure you have set up your .env file with PERPLEXITY_API_KEY
python example/example.py
```

This will:
1. Load sample Optimistic Oracle queries
2. Query the Perplexity API for each sample
3. Save results to the results directory 