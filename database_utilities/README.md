# UMA Oracle MongoDB Utilities

This directory contains utilities for importing UMA Oracle experiment results into MongoDB.

## Setup

1. Create a `.env` file in the project root directory with your MongoDB connection string:

```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database
```

2. Install the required dependencies:

```bash
pip install pymongo python-dotenv
```

## Usage Examples

### Import a single experiment

```bash
# Example Import the realtime follower experiment
python ./database_utilities/results_to_mongodb.py ./proposal_replayer/results/12032025-realtime-follower --database uma_oracle --collection experiments
```

### Import multiple experiments

```bash
# Import all experiments 
python ./database_utilities/batch_importer.py --all --results-dir ./proposal_replayer/results --database uma_oracle --collection experiments
```

## Available Utilities

### Single Experiment Import

The `results_to_mongodb.py` script imports a single experiment directory into MongoDB:

```bash
python results_to_mongodb.py /path/to/experiment/directory [--database name] [--collection name]
```

Options:
- `--database`: MongoDB database name (default: uma_oracle)
- `--collection`: MongoDB collection name (default: experiments)

### Batch Import

The `batch_importer.py` script can import multiple experiment directories at once:

```bash
# Import all experiments in the results directory
python batch_importer.py --all [--results-dir path] [--database name] [--collection name] [--workers num]

# Import specific experiment directories
python batch_importer.py --experiments exp1 exp2 [--results-dir path] [--database name] [--collection name] [--workers num]
```

Options:
- `--all`: Process all experiments in the results directory
- `--experiments`: Specific experiment directories to process (relative to results-dir)
- `--results-dir`: Path to the results directory (default: ../proposal_replayer/results)
- `--database`: MongoDB database name (default: uma_oracle)
- `--collection`: MongoDB collection name (default: experiments)
- `--workers`: Number of worker threads (default: 4)

### Prompt Import

The `prompts_to_mongodb.py` script extracts prompt templates from the codebase and imports them into MongoDB:

```bash
python ./database_utilities/prompts_to_mongodb.py [--database name]
```

Options:
- `--database`: MongoDB database name (default: uma_oracle)

This script extracts prompt templates from:
- The main `prompt.py` file (all prompt versions)
- The `prompt_overseer.py` file (overseer prompts)

The prompts are stored in a collection called `prompts` with the following structure:
```json
{
  "type": "main|overseer|overseer_base",
  "version": "v1|v2|v3",
  "is_latest": true|false,
  "template": "Source code of the prompt function",
  "example": "Example rendered prompt",
  "updated_at": "2025-03-25T12:34:56.789Z"
}
```

### Output Watcher

The `output_watcher.py` script monitors the outputs directory for new files and automatically imports them into MongoDB:

```bash
python ./database_utilities/output_watcher.py [--watch-dir path] [--database name] [--collection name] [--refresh-interval seconds]
```

Options:
- `--watch-dir`: Directory to watch for new experiment outputs (default: ../proposal_replayer/results)
- `--database`: MongoDB database name (default: uma_oracle)
- `--collection`: MongoDB collection name (default: experiments)
- `--refresh-interval`: Refresh interval in seconds for checking new experiment directories (default: 10)

The script:
1. Performs an initial import of all existing output files
2. Sets up file system watchers on all experiment output directories
3. Continuously monitors for new or modified files
4. Automatically imports new experiment directories as they're created
5. Updates MongoDB in real-time as new results are generated

This allows the Oracle system to write output files to disk normally, while the watcher handles MongoDB integration separately.

## Data Structure

The imported data follows this structure in MongoDB:

```json
{
  "experiment_id": "18032025-gpt-refined-prompt-realtime-follower",
  "metadata": {
    "experiment": {
      "timestamp": "18-03-2025 18:00",
      "title": "GPT Refined Prompt Realtime Follower",
      "goal": "...",
      "system_prompt": "...",
      "prompt_version": "v2",
      "setup": {
        "search_engine": "...",
        "model": "..."
      }
    }
  },
  "outputs": {
    "025eb1be": {
      "query_id": "0x025eb1bef9aa6a79a2d2e3a77ba937e8198cbd1debb6a0da38925898e9fb29ba",
      "question_id_short": "025eb1be",
      "transaction_hash": "0x6fb1bb90da68b789d384d17c0f80269db702cef1a1521034840aee8df88e56ed",
      "user_prompt": "...",
      "system_prompt": "...",
      "response": "...",
      "recommendation": "p4",
      "proposed_price": 1000000000000000000,
      "resolved_price": 1000000000000000000,
      "timestamp": 1741816977.1541991,
      "processed_file": "questionId_025eb1be.json",
      "response_metadata": {
        "model": "...",
        "created_timestamp": 1741816977,
        "created_datetime": "2025-03-12T23:02:57",
        "completion_tokens": 2459,
        "prompt_tokens": 577,
        "total_tokens": 3036,
        "api_response_time_seconds": 101.13006472587585
      },
      "citations": ["..."],
      "proposal_metadata": {...},
      "resolved_price_outcome": "p2",
      "disputed": false,
      "proposed_price_outcome": "p2",
      "tags": ["Sports", "Games", "CBB"]
    },
    "...": {...}
  }
}
```

Each experiment is stored as a single document, with all outputs nested within it. This structure makes it easy to retrieve entire experiments or specific outputs within an experiment.

## Notes

- If an experiment already exists in the database (matched by experiment_id), it will be updated rather than duplicated
- The import process validates experiment directories to ensure they have the correct structure before importing
- Logging is provided to track the import process and any errors that occur
- Parallel processing is used in the batch importer to speed up the import process
- Large integer values like `proposed_price` and `resolved_price` are automatically converted to strings to avoid MongoDB's 8-byte integer limit