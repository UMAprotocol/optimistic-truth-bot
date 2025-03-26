# UMA Proposal Replayer UI

A web interface for exploring UMA proposal outputs and reruns. Now with MongoDB integration for analytics data.

## Features

- View both outputs and reruns in a tabular format
- Search functionality to filter results
- Detailed view showing all information in each JSON file
- Easy navigation with clickable rows
- MongoDB integration for storing and retrieving analytics data

## Running the UI

### Option 1: Using the Python server (recommended)

1. Navigate to the UI directory:
   ```
   cd proposal_replayer/ui
   ```

2. Configure the MongoDB connection (if needed):
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your MongoDB connection details:
   ```
   MONGO_URI=mongodb://username:password@host:port/
   MONGODB_DB=your_database_name
   MONGODB_COLLECTION=your_collection_name
   ```

3. Run the server:
   ```
   python server.py
   ```

4. This will automatically open your browser to http://localhost:8000/ui/

### Option 2: Using any HTTP server

You can serve the UI directory with any HTTP server. For example:

```
cd proposal_replayer
python -m http.server
```

Then open your browser to http://localhost:8000/ui/

**Note**: MongoDB integration requires using the provided Python server from Option 1.

## MongoDB Integration

The UI now supports loading analytics data from MongoDB as well as from the filesystem. Here's how to use it:

### MongoDB Schema

Your MongoDB collection should have documents with the following structure:

```json
{
  "experiment_id": "unique-experiment-identifier",
  "experiment_title": "Your Experiment Title",
  "experiment_goal": "Experiment goals or description",
  "timestamp": "2023-01-01 12:00:00",
  "prompt": "Your prompt content",
  "response": "The LLM response",
  "recommendation": "The final recommendation",
  "resolution": true,
  "tags": ["tag1", "tag2"],
  "metadata": {
    // Any additional metadata
  }
}
```

The UI will automatically group documents by `experiment_id` and display them as separate experiments.

### Extended JSON Metadata Support

The UI now supports additional metadata fields from the JSON files:

- `expiration_timestamp`: Expiration time of the proposal
- `request_timestamp`: Request timestamp
- `request_transaction_block_time`: Block time of the request transaction
- `game_start_time`: Start time of the event/game
- `end_date_iso`: End date in ISO format
- `icon`: URL to the question icon

These fields are displayed in the details modal and can be filtered using the date filter controls. They can also be shown as columns in the results table via the column selector.

### Environment Variables

Configure the MongoDB connection using the following environment variables:

- `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017/`)
- `MONGODB_DB`: Database name (default: `uma_analytics`)
- `MONGODB_COLLECTION`: Collection name (default: `prompts`)

You can set these in a `.env` file in the repository root directory.

## Usage

1. The UI displays two tabs: "Analytics" and "Experiment Runner"
2. The Analytics tab shows experiments from both filesystem and MongoDB
3. Experiments from MongoDB are indicated with a database icon
4. Click on any experiment to view its results
5. Use the search box to filter results

## Development

The UI is built with:
- HTML/CSS/JavaScript
- Bootstrap 5 for styling
- MongoDB for data storage (optional)

Files:
- `index.html` - Main HTML structure
- `styles.css` - Custom CSS styles
- `app.js` - JavaScript for loading and displaying data
- `server.py` - Python server with MongoDB integration
- `.env.example` - Example environment configuration 