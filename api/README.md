# LLM Oracle API

This API provides access to the LLM Oracle experiment outputs stored in MongoDB. It allows querying by various parameters such as query_id, condition_id, transaction hash, timestamps, ancillary data, and more. The API is designed to make it easy to search and retrieve results from Oracle experiments through a RESTful interface.

## Overview

The LLM Oracle API serves as a query interface for the Oracle's experiment results stored in MongoDB. It enables:

- Searching by blockchain identifiers (query_id, condition_id, transaction_hash)
- Filtering by timestamp ranges
- Searching by content in ancillary data
- Filtering by recommendation outcomes (p1, p2, p3, p4)
- Retrieving results by experiment ID or question ID

## Setup

1. Ensure the MongoDB connection is configured in the `.env` file at the root of the repository:

```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB=uma_oracle
MONGODB_COLLECTION=experiments
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the API

From the repository root:

```bash
cd api
python main.py
```

Alternatively, use the provided convenience script:

```bash
./api/run_api.sh
```

By default, the API runs on port 8000. You can change this by setting the `PORT` environment variable in the `.env` file.

## Data Model

The API works with the following data model fields:

- `query_id`: The blockchain query identifier
- `transaction_hash`: The transaction hash from the blockchain
- `condition_id`: The blockchain condition identifier 
- `question_id`: The internal ID used to track the question
- `ancillary_data`: The ancillary data associated with the query
- `ancillary_data_hex`: Hexadecimal representation of the ancillary data
- `request_timestamp`: Unix timestamp when the request was made
- `tags`: Array of tags associated with the query
- `recommendation`: The final recommendation (p1, p2, p3, p4)

## API Endpoints

### Base URL: `https://api.llo.uma.xyz`

### Health Check

- **GET** `/`
  - Returns the API status
  - Example response: `{"status": "online", "message": "LLM Oracle API is running"}`

### Basic Query by Parameters

- **GET** `/api/query`
  - Query experiments by query_id, condition_id, or transaction hash
  - Parameters:
    - `query_id` (optional): Filter by query_id (exact match)
    - `condition_id` (optional): Filter by condition_id (exact match)
    - `transaction_hash` (optional): Filter by transaction hash (exact match)
    - `full` (optional, default=true): Return full JSON if true, reduced version if false
    - `limit` (optional, default=10): Maximum number of results to return
  - At least one of query_id, condition_id, or transaction_hash must be provided
  - Returns: Array of matching experiment outputs

### Advanced Query

- **GET** `/api/advanced-query`
  - Query experiments by multiple parameters including timestamps, ancillary data, and more
  - Parameters:
    - `identifier` (optional): Filter by partial match on tags, query_id, condition_id, etc.
    - `start_timestamp` (optional): Filter by minimum request timestamp (Unix timestamp)
    - `end_timestamp` (optional): Filter by maximum request timestamp (Unix timestamp)
    - `ancillary_data` (optional): Filter by partial match on ancillary data
    - `tags` (optional): Filter by one or more tags (can be repeated for multiple tags)
    - `recommendation` (optional): Filter by recommendation value (p1, p2, p3, p4)
    - `full` (optional, default=true): Return full JSON if true, reduced version if false
    - `limit` (optional, default=10): Maximum number of results to return
  - At least one filter parameter must be provided
  - Returns: Array of matching experiment outputs

- **POST** `/api/advanced-query`
  - Same functionality as the GET endpoint but accepts a JSON body
  - Request body example:
    ```json
    {
      "identifier": "Bitcoin",
      "start_timestamp": 1741964000,
      "end_timestamp": 1742148000,
      "ancillary_data": "Sample data",
      "tags": ["Crypto", "Bitcoin"],
      "recommendation": "p1",
      "full": true,
      "limit": 10
    }
    ```
  - All fields are optional, but at least one filter parameter must be provided
  - Returns: Array of matching experiment outputs
  - Especially useful for long queries with large ancillary data

### Get by Experiment ID

- **GET** `/api/experiment/{experiment_id}`
  - Get all questions for a specific experiment
  - Parameters:
    - `experiment_id` (required): The ID of the experiment (e.g., "08042025-multi-operator-with-realtime-bug-fix")
    - `full` (optional, default=true): Return full JSON if true, reduced version if false
    - `limit` (optional, default=100): Maximum number of results to return
  - Returns: Array of all questions/results from the specified experiment

### Get by Question ID

- **GET** `/api/question/{question_id}`
  - Get a specific question by its ID
  - Parameters:
    - `question_id` (required): The ID of the question (e.g., "result_21db972a_20250408_125019")
    - `full` (optional, default=true): Return full JSON if true, reduced version if false
  - Returns: Single JSON object containing the specified question data

## Example Usage

### Basic Query Examples

#### Query by query_id

```bash
curl 'https://api.llo.uma.xyz/api/query?query_id=0x21db972af5b6ac218f752a174751e0fb89164d2e574713d6162df5608afe87d2'
```

#### Query by transaction hash

```bash
curl 'https://api.llo.uma.xyz/api/query?transaction_hash=0x3372c0cfb782595199564a1436d1ed1f0d5fe2df931a562752790af2c817114a'
```

#### Query by condition_id with reduced output

```bash
curl 'https://api.llo.uma.xyz/api/query?condition_id=0x8de5bc7b33f71bbe8414d4daa1308cc19893fcf0012f41532643a2eb03ed28f4&full=false'
```

### Advanced Query Examples

#### Query by timestamp range

```bash
curl 'https://api.llo.uma.xyz/api/advanced-query?start_timestamp=1741964000&end_timestamp=1742148000'
```

#### Query by tags and recommendation

```bash
curl 'https://api.llo.uma.xyz/api/advanced-query?tags=Crypto&tags=Bitcoin&recommendation=p1'
```

#### Query by identifier (partial match)

```bash
curl 'https://api.llo.uma.xyz/api/advanced-query?identifier=Bitcoin'
```

#### Query by transaction hash (partial match)

```bash
curl 'https://api.llo.uma.xyz/api/advanced-query?identifier=0x3372c0cfb782'
```

#### Query by ancillary data (partial match)

```bash
curl 'https://api.llo.uma.xyz/api/advanced-query?ancillary_data=Sample'
```

#### Query with POST for large ancillary data

```bash
curl -X POST 'https://api.llo.uma.xyz/api/advanced-query' \
  -H 'Content-Type: application/json' \
  -d '{
    "start_timestamp": 1744617666,
    "ancillary_data": "0x713a207469746c653a20436f6c6f7261646f20526f636b696573..."
  }'
```

### Other Endpoint Examples

#### Get experiment by ID

```bash
curl 'https://api.llo.uma.xyz/api/experiment/08042025-multi-operator-with-realtime-bug-fix'
```

#### Get question by ID

```bash
curl 'https://api.llo.uma.xyz/api/question/result_21db972a_20250408_125019'
```

## Response Format

By default, the API returns the full JSON document for each query result. You can request a reduced version by setting the `full=false` parameter:

### Full response example (partial):
```json
{
  "_id": "65fe1902dd3a4e0012345678",
  "experiment_id": "04042025-multi-operator-realtime-follower",
  "question_id": "result_21db972a_20250408_125019",
  "query_id": "0x21db972af5b6ac218f752a174751e0fb89164d2e574713d6162df5608afe87d2",
  "condition_id": "0x8de5bc7b33f71bbe8414d4daa1308cc19893fcf0012f41532643a2eb03ed28f4",
  "recommendation": "p1",
  "disputed": false,
  "result": {
    "recommendation": "p1",
    "reason": "Based on the available information..."
  },
  "proposal_metadata": {
    "transaction_hash": "0xf2f4ebb8c3710d7476d18bc5b81ded2fdc4ff8f80a0005d75a7598994337d81d",
    "request_timestamp": 1741964809,
    "ancillary_data": "Sample ancillary data",
    "tags": ["Crypto", "Bitcoin"]
  }
}
```

### Reduced response example:
```json
{
  "_id": "65fe1902dd3a4e0012345678",
  "experiment_id": "04042025-multi-operator-realtime-follower",
  "question_id": "result_21db972a_20250408_125019",
  "query_id": "0x21db972af5b6ac218f752a174751e0fb89164d2e574713d6162df5608afe87d2",
  "condition_id": "0x8de5bc7b33f71bbe8414d4daa1308cc19893fcf0012f41532643a2eb03ed28f4",
  "recommendation": "p1",
  "disputed": false,
  "proposed_price_outcome": "p1",
  "resolved_price_outcome": null,
  "transaction_hash": "0xf2f4ebb8c3710d7476d18bc5b81ded2fdc4ff8f80a0005d75a7598994337d81d",
  "tags": ["Crypto", "Bitcoin"]
}
```