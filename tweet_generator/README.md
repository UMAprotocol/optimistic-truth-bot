# LLM Oracle Tweet Generator

This component generates and posts tweets about LLM Oracle predictions and outcomes. It regularly checks the Oracle API for new results and posts them to Twitter.

## Features

- Automatically generates tweets from Oracle prediction results
- Configurable posting schedule with cooldown periods
- Supports both Twitter API v1.1 (Tweepy) and v2
- Intelligent tweet content generation with hashtags
- Caching to reduce API load
- Robust error handling and logging
- Market ID deduplication to prevent duplicate tweets about the same market
- **Demo mode** - uses real data but only logs potential tweets to console (no actual posting)
- Mock mode for testing with simulated data

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to the LLM Oracle API
- Twitter API credentials (for posting tweets)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/large-language-oracle.git
   cd large-language-oracle
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install optional Twitter client libraries based on your needs:
   ```bash
   pip install tweepy        # For Twitter API v1.1
   # OR
   pip install twitter-api-client  # For Twitter API v2
   ```

4. Set up environment variables or create a configuration file:
   ```bash
   # Create a .env file in the project root
   touch .env
   ```

5. Edit the `.env` file with your API credentials:
   ```
   # Oracle API
   ORACLE_API_URL=https://api.ai.uma.xyz
   ORACLE_UI_URL=

   # Twitter API v1.1
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

   # Twitter API v2
   TWITTER_BEARER_TOKEN=your_bearer_token
   
   # Mode settings (set to "true" to enable)
   TWITTER_DEMO_MODE=true    # Demo mode - logs tweets to console
   TWITTER_TEST_MODE=false   # Test mode - uses mock data
   
   # Scheduler settings
   TWEET_CHECK_INTERVAL=300
   TWEET_COOLDOWN=3600
   TWEET_MAX_PER_DAY=48
   
   # Logging
   LOG_LEVEL=INFO
   LOG_FILE=logs/tweet_generator.log
   ```

## Usage

### Running the Tweet Generator

To run the tweet generator in the foreground:

```bash
python tweet_generator/run.py
```

To run in demo mode (no actual tweets posted, just console logging):

```bash
python tweet_generator/run.py --demo-mode
```

To run with specific options:

```bash
python tweet_generator/run.py --check-interval 600 --tweet-cooldown 7200 --max-tweets 24
```

### Configuration Options

You can configure the generator through:
- Environment variables
- Configuration file
- Command-line arguments

#### Command-line Arguments

- `--config`: Path to configuration file
- `--api-url`: Oracle API URL
- `--ui-url`: Oracle UI URL
- `--check-interval`: Interval between checks in seconds
- `--tweet-cooldown`: Minimum time between tweets in seconds
- `--max-tweets`: Maximum tweets per day
- `--lookback-hours`: Hours to look back for results
- `--state-file`: Path to state file
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--log-file`: Path to log file
- `--log-to-console`: Log to console
- `--no-log-to-console`: Don't log to console
- `--include-hashtags`: Include hashtags in tweets
- `--no-hashtags`: Don't include hashtags in tweets
- `--include-links`: Include links in tweets
- `--no-links`: Don't include links in tweets
- `--demo-mode`: Run in demo mode (don't actually post tweets, just log them)
- `--test-mode`: Run in test mode with mock data
- `--test-market-deduplication`: Test market deduplication with historical data

#### Configuration File Format

You can create a JSON configuration file:

```json
{
  "oracle_api_url": "https://api.ai.uma.xyz",
  "oracle_ui_url": "",
  "twitter_api_key": "",
  "twitter_api_secret": "",
  "twitter_access_token": "",
  "twitter_access_token_secret": "",
  "twitter_bearer_token": "",
  "twitter_demo_mode": true,
  "twitter_test_mode": false,
  "include_hashtags": true,
  "include_links": true,
  "max_tweet_length": 280,
  "check_interval": 300,
  "tweet_cooldown": 3600,
  "max_tweets_per_day": 48,
  "results_lookback_hours": 24,
  "state_file": "tweet_state.json",
  "log_level": "INFO",
  "log_file": "tweet_generator.log",
  "log_to_console": true
}
```

### Demo Mode

Demo mode is perfect for testing or development without actually posting to Twitter. In this mode:

1. The generator uses real data from the Oracle API
2. Tweets are generated with the actual content that would be posted
3. Instead of posting to Twitter, tweets are formatted and logged to the console
4. All generated tweets are also logged to the log file

### Market Deduplication Testing

You can test the market deduplication functionality with historical data:

```bash
python tweet_generator/run.py --test-market-deduplication --demo-mode
```

This will:
1. Fetch historical results from the Oracle API
2. Analyze the data for markets with multiple questions
3. Simulate the tweet filtering process
4. Log results showing which tweets would be posted and which would be skipped due to duplicate markets

To enable demo mode:

```bash
# Via command line
python tweet_generator/run.py --demo-mode

# Via environment variable
TWITTER_DEMO_MODE=true python tweet_generator/run.py

# Via config file
# In your JSON config, set: "twitter_demo_mode": true
```

Demo mode tweet output looks like:

```
============================================================
 DEMO TWEET - 2025-04-07 10:15:20
============================================================

LLM Oracle predicts: Will Ethereum dip to $1,500 by December 31? - Yes
#Crypto #Ethereum #eth #CryptoPrices #2025Predictions #LLMOracle #Prediction
https://example.com/question/024e024a

============================================================
```

### Running as a Service

For production use, it's recommended to run the tweet generator as a service.

#### Systemd (Linux)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/llm-oracle-tweets.service
```

Add the following content:

```
[Unit]
Description=LLM Oracle Tweet Generator
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/large-language-oracle
ExecStart=/path/to/python /path/to/large-language-oracle/tweet_generator/run.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=llm-oracle-tweets
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable llm-oracle-tweets
sudo systemctl start llm-oracle-tweets
```

To check the status:

```bash
sudo systemctl status llm-oracle-tweets
```

#### Docker

A Dockerfile is provided to containerize the application:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create directories for logs and state
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TWITTER_DEMO_MODE=true  # Set to false in production

# Run the application
CMD ["python", "tweet_generator/run.py"]
```

Build and run the Docker container:

```bash
docker build -t llm-oracle-tweets .
docker run -d --name oracle-tweets \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/tweet_state.json:/app/tweet_state.json \
  llm-oracle-tweets
```

## Testing

To run tests:

```bash
cd tweet_generator
python tests/run_tests.py
```

Or run individual test files:

```bash
python tests/test_tweet_content.py
python tests/test_oracle_api_client.py
python tests/test_twitter_client.py
```

## Module Structure

- `tweet_generator.py`: Main entry point and orchestration
- `oracle_api_client.py`: Client for interacting with the LLM Oracle API
- `tweet_content.py`: Logic for generating tweet content
- `twitter_client.py`: Interface to Twitter API
- `scheduler.py`: Scheduling logic for regular checks and posting
- `config.py`: Configuration management
- `logging_setup.py`: Logging configuration
- `tests/`: Test files

## Maintainers

If you encounter any issues or have questions, please contact the maintainers or file an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.