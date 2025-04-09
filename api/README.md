# LLM Oracle API

This API provides access to the LLM oracle experiment outputs stored in MongoDB. It allows querying by various parameters such as query_id, condition_id, and transaction hash.

## Setup

1. Ensure the MongoDB connection is configured in the `.env` file at the root of the repository:

```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB=uma_oracle
MONGODB_COLLECTION=experiments
```

2. Authentication is enabled by default. Configure the auth credentials in the `.env` file:

```
AUTH_ENABLED=true
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_password
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the API

From the repository root:

```bash
cd api
python main.py
```

By default, the API runs on port 8000. You can change this by setting the `PORT` environment variable in the `.env` file.

## API Endpoints

### Base URL: `http://localhost:8000`

### Authentication

All endpoints require Basic Authentication if `AUTH_ENABLED` is set to `true` in the `.env` file.

### Health Check

- **GET** `/`
  - Returns the API status

### Query by Parameters

- **GET** `/api/query`
  - Query experiments by query_id, condition_id, or transaction hash
  - Parameters:
    - `query_id` (optional): Filter by query_id
    - `condition_id` (optional): Filter by condition_id
    - `transaction_hash` (optional): Filter by transaction hash
    - `full` (optional, default=true): Return full JSON if true, reduced version if false
    - `limit` (optional, default=10): Maximum number of results to return
  - At least one of query_id, condition_id, or transaction_hash must be provided

### Get by Experiment ID

- **GET** `/api/experiment/{experiment_id}`
  - Get all questions for a specific experiment
  - Parameters:
    - `experiment_id` (required): The ID of the experiment
    - `full` (optional, default=true): Return full JSON if true, reduced version if false
    - `limit` (optional, default=100): Maximum number of results to return

### Get by Question ID

- **GET** `/api/question/{question_id}`
  - Get a specific question by its ID
  - Parameters:
    - `question_id` (required): The ID of the question
    - `full` (optional, default=true): Return full JSON if true, reduced version if false

## Example Usage

### Query by query_id

```
GET /api/query?query_id=0x21db972af5b6ac218f752a174751e0fb89164d2e574713d6162df5608afe87d2
```

### Query by condition_id with reduced output

```
GET /api/query?condition_id=0x8de5bc7b33f71bbe8414d4daa1308cc19893fcf0012f41532643a2eb03ed28f4&full=false
```

### Get experiment by ID

```
GET /api/experiment/08042025-multi-operator-with-realtime-bug-fix
```

### Get question by ID

```
GET /api/question/result_21db972a_20250408_125019
``` 