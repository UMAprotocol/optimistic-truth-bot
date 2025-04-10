#!/usr/bin/env python3
"""
Simple HTTP server for the Large Language Oracle Results Analyzer
Usage: python server.py
"""

import http.server
import socketserver
import os
import webbrowser
import time
import threading
import json
import uuid
import subprocess
import shlex
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import select
import fcntl
import errno
import urllib.parse
import re
import sys
import pymongo
from pymongo import MongoClient

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load .env from the correct repository directory (root directory)
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment variables from {env_path}")
except ImportError:
    print(
        "Warning: python-dotenv not installed. Environment variables from .env file will not be loaded."
    )
    print("Install with: pip install python-dotenv")
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Configuration
PORT = 8000
PARENT_DIR = Path(__file__).parent.parent
UI_DIR = Path(__file__).parent
RESULTS_DIR = PARENT_DIR / "results"
LOG_DIR = PARENT_DIR / "logs"
OUTPUTS_DIR = PARENT_DIR / "proposal_overseer" / "outputs"
RERUNS_DIR = PARENT_DIR / "proposal_overseer" / "reruns"
# Base repository directory (one level up from proposal_replayer)
BASE_REPO_DIR = PARENT_DIR

# MongoDB configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.environ.get("MONGODB_DB", "uma_analytics")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "prompts")
MONGO_ONLY_RESULTS = os.environ.get("MONGO_ONLY_RESULTS", "false").lower() == "true"

# Define outputs collection name based on main collection
MONGODB_OUTPUTS_COLLECTION = f"{MONGODB_COLLECTION}_outputs"

# Experiment runner configuration
DISABLE_EXPERIMENT_RUNNER = (
    os.environ.get("DISABLE_EXPERIMENT_RUNNER", "false").lower() == "true"
)

# Authentication settings - Change these!
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "true").lower() == "true"
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "password123")
AUTH_TOKEN_SECRET = os.environ.get("AUTH_TOKEN_SECRET", "change-this-secret-key")

# Ensure required directories exist
LOG_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)
RERUNS_DIR.mkdir(exist_ok=True)

# Global variables
server = None
observer = None
restart_event = threading.Event()

# Process management
active_processes = {}
process_logs = {}
process_lock = threading.Lock()

# MongoDB connection
mongodb_client = None
mongodb_db = None


def get_mongodb_connection():
    """Get or create the MongoDB connection"""
    global mongodb_client, mongodb_db

    if mongodb_client is None:
        try:
            logger.info(f"Connecting to MongoDB at {MONGO_URI}")
            # Set a shorter client timeout to avoid application hanging
            mongodb_client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 seconds timeout instead of default 30s
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
            )
            # Verify connection by querying server info
            mongodb_client.server_info()  # This will raise an exception if connection fails
            mongodb_db = mongodb_client[MONGODB_DB]
            logger.info(f"Connected to MongoDB, database: {MONGODB_DB}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            mongodb_client = None
            mongodb_db = None

    return mongodb_db


# Process output reader thread
def read_process_output(process, process_id):
    """Read and log output from a running process in real-time"""
    # Set stdout and stderr to non-blocking mode
    for pipe in [process.stdout, process.stderr]:
        fd = pipe.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    # Buffers for partial lines
    stdout_buffer = b""
    stderr_buffer = b""

    # Continue as long as the process is running
    while process.poll() is None:
        # Use select to wait for data with a timeout
        ready_to_read, _, _ = select.select(
            [process.stdout, process.stderr], [], [], 0.1
        )

        for pipe in ready_to_read:
            # Read available data
            try:
                data = pipe.read(4096)  # Read up to 4KB at a time
                if not data:  # EOF
                    continue

                buffer = stdout_buffer if pipe == process.stdout else stderr_buffer
                buffer += data

                # Process complete lines but also partial data if we have some
                # First check if we have any newlines
                if b"\n" in buffer:
                    lines = buffer.split(b"\n")
                    # Last element is a partial line or empty
                    if pipe == process.stdout:
                        stdout_buffer = lines[-1]
                        complete_lines = lines[:-1]
                    else:
                        stderr_buffer = lines[-1]
                        complete_lines = lines[:-1]

                    # Process each complete line
                    for line in complete_lines:
                        process_log_line(process_id, line, pipe == process.stdout)
                else:
                    # Also handle partial data even without newlines
                    # (useful for single-character streaming)
                    if len(buffer) > 0:
                        process_log_line(process_id, buffer, pipe == process.stdout)
                        if pipe == process.stdout:
                            stdout_buffer = b""
                        else:
                            stderr_buffer = b""

            except (IOError, OSError) as e:
                # Handle pipe errors (e.g., when process terminates during read)
                if e.errno != errno.EAGAIN:
                    logger.error(f"Error reading from pipe: {e}")

        # Small sleep to prevent CPU spinning
        time.sleep(0.01)

    # Handle any remaining data in buffers - rest of function unchanged
    # ...


# Helper function to process a line of output
def process_log_line(process_id, line_bytes, is_stdout=True):
    if not line_bytes:  # Skip empty lines
        return

    line_str = line_bytes.decode("utf-8", errors="replace").rstrip()
    timestamp = int(time.time())
    log_type = "info" if is_stdout else "error"

    log_entry = {
        "timestamp": timestamp,
        "message": line_str,
        "type": log_type,
    }

    # Add to in-memory logs
    with process_lock:
        if process_id in process_logs:
            process_logs[process_id].append(log_entry)
        else:
            process_logs[process_id] = [log_entry]

    # Write to log file
    log_file = LOG_DIR / f"process_{process_id}.log"
    try:
        with open(log_file, "a") as f:
            f.write(
                f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] {line_str}\n"
            )
            f.flush()  # Ensure it's written immediately
    except Exception as e:
        logger.error(f"Error writing to log file: {e}")

    logger.debug(f"Process {process_id} output: {line_str}")


# Process monitor thread to check for completed processes
def monitor_processes():
    """Monitor running processes and update their status"""
    while True:
        try:
            time.sleep(2)  # Check every 2 seconds

            with process_lock:
                for process_id, process_info in list(active_processes.items()):
                    if (
                        process_info["status"] == "running"
                        and "process" in process_info
                    ):
                        # Check if process is still running
                        exit_code = process_info["process"].poll()
                        if exit_code is not None:
                            # Process has completed
                            status = "completed" if exit_code == 0 else "failed"
                            active_processes[process_id]["status"] = status

                            status_message = (
                                "completed successfully"
                                if exit_code == 0
                                else f"failed with exit code {exit_code}"
                            )
                            log_entry = {
                                "timestamp": int(time.time()),
                                "message": f"Process {status_message}",
                                "type": "info" if exit_code == 0 else "error",
                            }

                            if process_id in process_logs:
                                process_logs[process_id].append(log_entry)
                            else:
                                process_logs[process_id] = [log_entry]

                            logger.info(f"Process {process_id} {status_message}")
        except Exception as e:
            logger.error(f"Error in process monitor: {e}")


# Start process monitor thread
process_monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
process_monitor_thread.start()


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Custom log formatting
        logger.info(f"{self.address_string()} - {format % args}")

    def send_static_file(self, file_path):
        """Send a static file to the client with appropriate headers"""
        try:
            # Determine content type based on file extension
            content_type = "application/octet-stream"  # Default
            if file_path.endswith(".html"):
                content_type = "text/html"
            elif file_path.endswith(".css"):
                content_type = "text/css"
            elif file_path.endswith(".js"):
                content_type = "application/javascript"
            elif file_path.endswith(".json"):
                content_type = "application/json"
            elif file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif file_path.endswith(".svg"):
                content_type = "image/svg+xml"
            elif file_path.endswith(".ico"):
                content_type = "image/x-icon"
            elif file_path.endswith(".txt"):
                content_type = "text/plain"

            # Get file size
            file_size = os.path.getsize(file_path)

            # Send headers
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.end_headers()

            # Send file content
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())

        except Exception as e:
            logger.error(f"Error sending static file {file_path}: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"error": f"Error serving file: {str(e)}"}).encode()
            )

    def is_authenticated(self):
        """Check if the request is authenticated"""
        if not AUTH_ENABLED:
            return True

        # Check for auth cookie
        cookies_header = self.headers.get("Cookie", "")
        cookies = {}
        for cookie in cookies_header.split(";"):
            if "=" in cookie:
                name, value = cookie.strip().split("=", 1)
                cookies[name] = value

        auth_token = cookies.get("auth_token", "")

        # Very simple token validation
        import hashlib
        import hmac

        # Create expected token
        expected = hmac.new(
            AUTH_TOKEN_SECRET.encode(),
            f"{AUTH_USERNAME}:{AUTH_PASSWORD}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(auth_token, expected)

    def serve_login_page(self):
        """Serve the login page"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        login_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - 🔮 Large Language Oracle</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    background-color: #f8f9fa;
                    height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .login-container {{
                    max-width: 400px;
                    padding: 15px;
                    margin: 0 auto;
                }}
                .login-header {{
                    background-color: #ec5b54;
                    color: white;
                    padding: 20px;
                    border-radius: 5px 5px 0 0;
                    text-align: center;
                }}
                .login-form {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .error-message {{
                    color: #dc3545;
                    margin-bottom: 15px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="login-header">
                    <h2>🔮 Large Language Oracle</h2>
                </div>
                <div class="login-form">
                    <div id="errorMessage" class="error-message" style="display: none;">
                        Invalid username or password
                    </div>
                    <form id="loginForm">
                        <div class="mb-3">
                            <label for="username" class="form-label">Username</label>
                            <input type="text" class="form-control" id="username" required>
                        </div>
                        <div class="mb-3">
                            <label for="password" class="form-label">Password</label>
                            <input type="password" class="form-control" id="password" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Login</button>
                    </form>
                </div>
            </div>
            
            <script>
                document.getElementById('loginForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    
                    try {{
                        const response = await fetch('/api/login', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{ username, password }})
                        }});
                        
                        if (response.ok) {{
                            const data = await response.json();
                            document.cookie = `auth_token=${{data.token}}; path=/; max-age=86400`;
                            window.location.href = '/';
                        }} else {{
                            document.getElementById('errorMessage').style.display = 'block';
                        }}
                    }} catch (error) {{
                        console.error('Login error:', error);
                        document.getElementById('errorMessage').style.display = 'block';
                    }}
                }});
            </script>
        </body>
        </html>
        """

        self.wfile.write(login_html.encode())

    def do_GET(self):
        """Handle GET requests."""
        try:
            # First handle the login page specially to avoid redirect loops
            if self.path == "/login":
                self.serve_login_page()
                return

            # Handle static assets that should be accessible without auth
            is_login_api = self.path == "/api/login"
            is_static_asset = self.path.endswith(
                (
                    ".css",
                    ".js",
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".ico",
                    ".svg",
                    ".woff",
                    ".woff2",
                )
            )

            # If not authenticated and not requesting login-related resources, redirect to login
            if not self.is_authenticated() and not (is_login_api or is_static_asset):
                logger.info(
                    f"Redirecting unauthenticated request to login: {self.path}"
                )
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return

            # Static file handling
            if self.path == "/" or self.path == "":
                self.path = "/index.html"

            # Serve static files
            if not self.path.startswith("/api/"):
                # Adjust to find files in ui directory
                if self.path.startswith("/"):
                    path_without_prefix = self.path[1:]
                else:
                    path_without_prefix = self.path

                # Try ui directory first
                file_path = os.path.join(os.path.dirname(__file__), path_without_prefix)
                if os.path.isfile(file_path):
                    self.send_static_file(file_path)
                    return

                # If not found in ui directory, try working directory
                file_path = os.path.join(os.getcwd(), path_without_prefix)
                if os.path.isfile(file_path):
                    self.send_static_file(file_path)
                    return

            # API endpoints
            if self.path == "/api/config":
                try:
                    config = {
                        "mongo_only_results": MONGO_ONLY_RESULTS,
                        "mongodb_db": MONGODB_DB,
                        "auth_enabled": AUTH_ENABLED,
                        "disable_experiment_runner": DISABLE_EXPERIMENT_RUNNER,
                    }

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(config).encode())
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    error_message = f"Error getting server configuration: {str(e)}"
                    logger.error(error_message)
                    self.wfile.write(json.dumps({"error": error_message}).encode())
                    return

            elif self.path == "/api/processes":
                if not self.is_authenticated():
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                    return

                # Check if experiment runner is disabled
                if DISABLE_EXPERIMENT_RUNNER:
                    self.send_response(403)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": "Experiment runner is disabled"}).encode()
                    )
                    return

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                with process_lock:
                    processes_list = []
                    for process_id, process_info in active_processes.items():
                        process_data = {
                            "id": process_id,
                            "command": process_info.get("command", ""),
                            "start_time": process_info.get("start_time", 0),
                            "status": process_info.get("status", "unknown"),
                        }

                        if process_id in process_logs:
                            process_data["logs"] = process_logs[process_id]
                        else:
                            process_data["logs"] = []

                        processes_list.append(process_data)

                self.wfile.write(json.dumps(processes_list).encode())
                return

            # API endpoint for specific process logs
            elif self.path.startswith("/api/process/"):
                try:
                    # Extract process ID from the URL
                    process_id = self.path.split("/")[-1]

                    with process_lock:
                        # First check if it's an active process
                        if process_id in active_processes:
                            process_data = {
                                "id": process_id,
                                "command": active_processes[process_id].get(
                                    "command", ""
                                ),
                                "start_time": active_processes[process_id].get(
                                    "start_time", 0
                                ),
                                "status": active_processes[process_id].get(
                                    "status", "unknown"
                                ),
                            }

                            if process_id in process_logs:
                                process_data["logs"] = process_logs[process_id]
                            else:
                                process_data["logs"] = []

                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(json.dumps(process_data).encode())
                            return

                    # If not an active process, try to find logs in the log file
                    log_file = LOG_DIR / f"{process_id}.log"
                    if not log_file.exists():
                        # Try alternative format with process_ prefix
                        log_file = LOG_DIR / f"process_{process_id}.log"

                    if log_file.exists():
                        # Parse the log file into log entries
                        logs = []
                        command = None
                        start_time = 0
                        status = "completed"  # Default status for historical logs

                        try:
                            with open(log_file, "r") as f:
                                for line in f:
                                    try:
                                        # Try to parse the timestamp from the line
                                        timestamp_match = re.match(
                                            r"\[(.*?)\] (.*)", line
                                        )
                                        if timestamp_match:
                                            timestamp_str = timestamp_match.group(1)
                                            message = timestamp_match.group(2)

                                            # Try different timestamp formats
                                            timestamp = 0
                                            try:
                                                # Try standard format "2023-01-01 12:34:56"
                                                timestamp = int(
                                                    datetime.strptime(
                                                        timestamp_str,
                                                        "%Y-%m-%d %H:%M:%S",
                                                    ).timestamp()
                                                )
                                            except ValueError:
                                                try:
                                                    # Try time-only format "12:34:56.789"
                                                    current_date = (
                                                        datetime.now().strftime(
                                                            "%Y-%m-%d"
                                                        )
                                                    )
                                                    timestamp = int(
                                                        datetime.strptime(
                                                            f"{current_date} {timestamp_str.split('.')[0]}",
                                                            "%Y-%m-%d %H:%M:%S",
                                                        ).timestamp()
                                                    )
                                                except ValueError:
                                                    # Use current timestamp as fallback
                                                    timestamp = int(time.time())

                                            # Determine the log type based on content
                                            log_type = "info"
                                            if (
                                                "ERROR" in line
                                                or "failed" in line.lower()
                                                or "error" in line.lower()
                                            ):
                                                log_type = "error"
                                                if "Process failed" in message:
                                                    status = "failed"
                                            elif (
                                                "WARNING" in line
                                                or "stopped" in line.lower()
                                            ):
                                                log_type = "warning"
                                                if "Process stopped" in message:
                                                    status = "stopped"

                                            # Extract command from the first line if it's a "Starting process" line
                                            if not command and (
                                                "Starting process" in message
                                                or "Running command" in message
                                            ):
                                                command_match = re.search(
                                                    r"(Starting process|Running command): (.*)",
                                                    message,
                                                )
                                                if command_match:
                                                    command = command_match.group(2)
                                                    if not start_time:
                                                        start_time = timestamp

                                            logs.append(
                                                {
                                                    "timestamp": timestamp,
                                                    "message": message,
                                                    "type": log_type,
                                                }
                                            )
                                        else:
                                            # If line doesn't match timestamp format, add it as-is
                                            logs.append(
                                                {
                                                    "timestamp": int(time.time()),
                                                    "message": line.strip(),
                                                    "type": "info",
                                                }
                                            )
                                    except Exception as parse_error:
                                        logger.error(
                                            f"Error parsing log line: {parse_error}"
                                        )
                                        # Still include the line even if parsing fails
                                        logs.append(
                                            {
                                                "timestamp": int(time.time()),
                                                "message": line.strip(),
                                                "type": "info",
                                            }
                                        )
                        except Exception as file_error:
                            logger.error(f"Error reading log file: {file_error}")

                        # If we couldn't extract a command from the logs, use the process ID
                        if not command:
                            command = f"Process {process_id}"

                        # Create a process data object from the parsed logs
                        process_data = {
                            "id": process_id,
                            "command": command,
                            "start_time": start_time
                            or int(time.time()) - 3600,  # Default to 1 hour ago
                            "status": status,
                            "logs": logs,
                        }

                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps(process_data).encode())
                        return

                    # If we get here, the process was not found
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": "Process not found"}).encode()
                    )
                    return
                except Exception as e:
                    logger.error(f"Error fetching process logs: {e}")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return

            # MongoDB API endpoint for analytics
            elif self.path == "/api/mongodb/analytics":
                if not self.is_authenticated():
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                    return

                try:
                    db = get_mongodb_connection()
                    if db is None:
                        self.send_response(500)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "MongoDB connection failed"}).encode()
                        )
                        return

                    # Parse query parameters
                    parsed_url = urllib.parse.urlparse(self.path)
                    params = urllib.parse.parse_qs(parsed_url.query)

                    # Set up query filters
                    query = {}

                    # Fetch all analytics from MongoDB
                    collection = db[MONGODB_COLLECTION]
                    outputs_collection = db[MONGODB_OUTPUTS_COLLECTION]

                    # Get experiment metadata
                    experiment_docs = list(collection.find(query, {"_id": 0}))

                    # Initialize experiments dictionary
                    experiments = {}

                    # First add metadata for all experiments
                    for exp in experiment_docs:
                        experiment_id = exp.get("experiment_id", "unknown")
                        metadata = exp.get("metadata", {})

                        if experiment_id not in experiments:
                            experiments[experiment_id] = {
                                "directory": experiment_id,
                                "path": f"mongodb/{experiment_id}",
                                "title": metadata.get("experiment", {}).get(
                                    "title", experiment_id
                                ),
                                "timestamp": metadata.get("experiment", {}).get(
                                    "timestamp", ""
                                ),
                                "goal": metadata.get("experiment", {}).get("goal", ""),
                                "count": 0,
                                "metadata": metadata,
                            }

                    # Now get output counts for each experiment
                    for exp_id in experiments:
                        output_count = outputs_collection.count_documents(
                            {"experiment_id": exp_id}
                        )
                        experiments[exp_id]["count"] = output_count

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(list(experiments.values())).encode())
                    return

                except Exception as e:
                    logger.error(f"Error fetching from MongoDB: {e}")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return

            # MongoDB API endpoint for a specific experiment
            elif self.path.startswith("/api/mongodb/experiment/"):
                if not self.is_authenticated():
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                    return

                try:
                    # Extract experiment ID from the URL
                    experiment_id = self.path.split("/")[-1]
                    parsed_url = urllib.parse.urlparse(self.path)
                    params = urllib.parse.parse_qs(parsed_url.query)

                    db = get_mongodb_connection()
                    if db is None:
                        self.send_response(500)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "MongoDB connection failed"}).encode()
                        )
                        return

                    # Query MongoDB for all entries matching this experiment ID
                    collection = db[MONGODB_COLLECTION]
                    outputs_collection = db[MONGODB_OUTPUTS_COLLECTION]

                    # Get experiment metadata
                    exp_metadata = collection.find_one(
                        {"experiment_id": experiment_id}, {"_id": 0}
                    )

                    # Get all outputs for this experiment
                    outputs = list(
                        outputs_collection.find(
                            {"experiment_id": experiment_id}, {"_id": 0}
                        )
                    )

                    # Process results to handle the new structure
                    processed_results = []

                    if not exp_metadata:
                        logger.warning(
                            f"No metadata found for experiment {experiment_id}"
                        )
                        exp_metadata = {"experiment_id": experiment_id, "metadata": {}}

                    # Extract experiment metadata
                    experiment_metadata = exp_metadata.get("metadata", {}).get(
                        "experiment", {}
                    )

                    # Process each output
                    for output in outputs:
                        # Create processed item with experiment metadata and output data
                        processed_item = {
                            # Add experiment metadata
                            "experiment_id": experiment_id,
                            "experiment_title": experiment_metadata.get("title", ""),
                            "experiment_goal": experiment_metadata.get("goal", ""),
                            "timestamp": output.get(
                                "timestamp", experiment_metadata.get("timestamp", "")
                            ),
                            # Add output data
                            **output,
                            # Add metadata for reference
                            "metadata": {
                                "experiment": experiment_metadata,
                                "setup": exp_metadata.get("metadata", {}).get(
                                    "setup", {}
                                ),
                                "modifications": exp_metadata.get("metadata", {}).get(
                                    "modifications", {}
                                ),
                            },
                        }
                        processed_results.append(processed_item)

                    # Log the processed results
                    logger.info(
                        f"MongoDB experiment {experiment_id} processed {len(processed_results)} results"
                    )

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(processed_results).encode())
                    return

                except Exception as e:
                    logger.error(f"Error fetching experiment from MongoDB: {e}")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return

            # Special handling for results directory files
            if self.path.startswith("/results/"):
                # Remap the path to the actual results directory
                file_path = PARENT_DIR / self.path[1:]  # Remove leading slash
                logger.info(f"Accessing result file: {self.path}")
                logger.info(f"Mapped to: {file_path}")
                logger.info(f"File exists: {file_path.exists()}")

                try:
                    if file_path.exists() and file_path.is_file():
                        logger.info(f"Serving file: {file_path}")
                        self.send_response(200)
                        # Set the appropriate content type
                        if file_path.suffix == ".json":
                            self.send_header("Content-Type", "application/json")
                        elif file_path.suffix == ".txt":
                            self.send_header("Content-Type", "text/plain")
                        else:
                            self.send_header("Content-Type", "application/octet-stream")

                        # Set content length
                        self.send_header(
                            "Content-Length", str(file_path.stat().st_size)
                        )
                        self.end_headers()

                        # Send the file contents
                        with open(file_path, "rb") as f:
                            self.wfile.write(f.read())
                        return
                    else:
                        logger.error(f"File not found: {file_path}")
                        # Check if directory exists but file doesn't
                        if file_path.parent.exists():
                            logger.info(f"Directory exists: {file_path.parent}")
                            logger.info(
                                f"Directory contents: {list(file_path.parent.iterdir())}"
                            )

                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "File not found"}).encode()
                        )
                        return
                except Exception as e:
                    logger.error(f"Error serving file {file_path}: {e}")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return

            # API endpoint for results directories (both filesystem and MongoDB)
            elif self.path == "/api/results-directories":
                try:
                    results = []

                    # First get results from filesystem (only if MONGO_ONLY_RESULTS is False)
                    if not MONGO_ONLY_RESULTS:
                        for dir_path in RESULTS_DIR.iterdir():
                            if dir_path.is_dir():
                                metadata_file = dir_path / "metadata.json"
                                outputs_dir = dir_path / "outputs"

                                # Count the number of JSON files in the outputs directory
                                file_count = 0
                                if outputs_dir.exists() and outputs_dir.is_dir():
                                    file_count = len(
                                        [
                                            f
                                            for f in outputs_dir.iterdir()
                                            if f.is_file()
                                            and f.suffix.lower() == ".json"
                                        ]
                                    )

                                if metadata_file.exists():
                                    with open(metadata_file, "r") as f:
                                        metadata = json.load(f)

                                    result = {
                                        "directory": dir_path.name,
                                        "path": f"results/{dir_path.name}",
                                        "title": metadata.get("experiment", {}).get(
                                            "title", dir_path.name
                                        ),
                                        "timestamp": metadata.get("experiment", {}).get(
                                            "timestamp", ""
                                        ),
                                        "goal": metadata.get("experiment", {}).get(
                                            "goal", ""
                                        ),
                                        "count": file_count,
                                        "metadata": metadata,
                                        "source": "filesystem",
                                    }
                                    results.append(result)
                                else:
                                    # If no metadata file exists, use directory name
                                    results.append(
                                        {
                                            "directory": dir_path.name,
                                            "path": f"results/{dir_path.name}",
                                            "title": dir_path.name,
                                            "timestamp": "",
                                            "goal": "",
                                            "count": file_count,
                                            "source": "filesystem",
                                        }
                                    )

                    # Then try to get results from MongoDB
                    mongo_error_info = None
                    try:
                        db = get_mongodb_connection()
                        if db is not None:
                            collection = db[MONGODB_COLLECTION]
                            outputs_collection = db[MONGODB_OUTPUTS_COLLECTION]

                            # Get all unique experiments
                            experiments = collection.find(
                                {},
                                {
                                    "experiment_id": 1,
                                    "metadata.experiment": 1,
                                    "_id": 0,
                                },
                            )

                            # Process each unique experiment
                            for exp in experiments:
                                experiment_id = exp.get("experiment_id")
                                if not experiment_id:
                                    continue

                                # Get experiment metadata
                                metadata = exp.get("metadata", {}).get("experiment", {})

                                # Count outputs for this experiment
                                output_count = outputs_collection.count_documents(
                                    {"experiment_id": experiment_id}
                                )

                                results.append(
                                    {
                                        "directory": experiment_id,
                                        "path": f"mongodb/{experiment_id}",
                                        "title": metadata.get("title", experiment_id),
                                        "timestamp": metadata.get("timestamp", ""),
                                        "goal": metadata.get("goal", ""),
                                        "count": output_count,
                                        "source": "mongodb",
                                    }
                                )
                    except Exception as mongo_error:
                        logger.error(
                            f"Error getting MongoDB experiments: {mongo_error}"
                        )
                        # Save the error info to include in the response
                        mongo_error_info = {
                            "mongo_error": str(mongo_error),
                            "mongo_status": "unavailable",
                        }
                        # Continue with filesystem results even if MongoDB fails

                    # Return the response with filesystem data and optional MongoDB error info
                    response_data = results
                    if mongo_error_info:
                        # Add MongoDB error info to the response
                        response_data = {
                            "results": results,
                            "mongo_status": "error",
                            "mongo_error": mongo_error_info["mongo_error"],
                            "mongo_only_results": MONGO_ONLY_RESULTS,
                        }
                    else:
                        # Add mongo_only_results flag to the response
                        response_data = {
                            "results": results,
                            "mongo_only_results": MONGO_ONLY_RESULTS,
                        }

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                    return
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    error_message = f"Error processing results directories: {str(e)}"
                    logger.error(error_message)
                    import traceback

                    logger.error(traceback.format_exc())
                    self.wfile.write(json.dumps({"error": error_message}).encode())
                    return

            # API endpoint to list files in a directory
            elif self.path.startswith("/api/files"):
                try:
                    # Parse the query parameter
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)
                    dir_path = params.get("path", [""])[0]

                    if not dir_path:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "path parameter is required"}).encode()
                        )
                        return

                    # Sanitize path to prevent directory traversal
                    safe_path = os.path.normpath(dir_path).lstrip("/")
                    full_path = PARENT_DIR / safe_path
                    logger.info(f"Listing files in directory: {full_path}")

                    # Check if the directory exists
                    if not full_path.exists():
                        logger.error(f"Path not found: {full_path}")
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"error": "Path not found", "path": safe_path}
                            ).encode()
                        )
                        return

                    if full_path.is_dir():
                        # List all files in the directory with metadata
                        files = []
                        for item in full_path.iterdir():
                            file_info = {
                                "name": item.name,
                                "path": str(Path(safe_path) / item.name).replace(
                                    "\\", "/"
                                ),
                                "type": "directory" if item.is_dir() else "file",
                            }

                            # Only get size for files, not directories
                            if item.is_file():
                                file_info["size"] = item.stat().st_size
                                # For JSON files, include file type explicitly
                                if item.suffix.lower() == ".json":
                                    file_info["file_type"] = "json"

                            files.append(file_info)

                        logger.info(f"Found {len(files)} items in {full_path}")

                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"files": files, "path": safe_path, "count": len(files)}
                            ).encode()
                        )
                    else:
                        # If it's a file, return its metadata
                        file_info = {
                            "name": full_path.name,
                            "path": safe_path,
                            "type": "file",
                            "size": full_path.stat().st_size,
                        }
                        if full_path.suffix.lower() == ".json":
                            file_info["file_type"] = "json"

                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"file": file_info, "path": safe_path}).encode()
                        )

                    return
                except Exception as e:
                    logger.error(f"Error listing files: {e}")
                    import traceback

                    logger.error(traceback.format_exc())
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return

            # API endpoint to retrieve multiple files in a batch
            elif self.path.startswith("/api/batch-files"):
                try:
                    # Parse the query parameters
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)

                    logger.info(f"Batch files request with params: {params}")

                    # Get the base directory
                    base_dir = params.get("dir", [""])[0]
                    if not base_dir:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "dir parameter is required"}).encode()
                        )
                        return

                    # Get the list of filenames
                    files_param = params.get("files", [""])[0]
                    if not files_param:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"error": "files parameter is required"}
                            ).encode()
                        )
                        return

                    # Parse the comma-separated list of filenames
                    filenames = files_param.split(",")
                    if not filenames:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"error": "No valid filenames provided"}
                            ).encode()
                        )
                        return

                    # Sanitize base directory path and ensure it starts with 'results/'
                    safe_base_dir = os.path.normpath(base_dir).lstrip("/")
                    if not safe_base_dir.startswith("results/"):
                        safe_base_dir = f"results/{safe_base_dir}"

                    # Try different path combinations to find the right one
                    possible_paths = [
                        PARENT_DIR / safe_base_dir,
                        PARENT_DIR / Path(safe_base_dir),
                        (
                            PARENT_DIR
                            / "results"
                            / Path(safe_base_dir).relative_to(Path("results"))
                            if safe_base_dir.startswith("results/")
                            else None
                        ),
                        Path(safe_base_dir),
                        BASE_REPO_DIR / safe_base_dir,
                    ]

                    full_base_dir = None
                    for path in possible_paths:
                        if path and path.exists() and path.is_dir():
                            full_base_dir = path
                            logger.info(f"Found valid directory path: {full_base_dir}")
                            break

                    if not full_base_dir:
                        # If no valid path found, use the original calculation
                        full_base_dir = PARENT_DIR / safe_base_dir

                    # Log all the paths we tried
                    logger.info(f"Original dir parameter: {base_dir}")
                    logger.info(f"Sanitized dir path: {safe_base_dir}")
                    logger.info(f"Final full path: {full_base_dir}")
                    logger.info(f"Path exists: {full_base_dir.exists()}")
                    logger.info(
                        f"Path is dir: {full_base_dir.is_dir() if full_base_dir.exists() else False}"
                    )
                    logger.info(f"Current working directory: {os.getcwd()}")
                    logger.info(f"PARENT_DIR: {PARENT_DIR}")

                    # List directory contents if it exists
                    if full_base_dir.exists() and full_base_dir.is_dir():
                        logger.info(
                            f"Directory contents: {[f.name for f in full_base_dir.iterdir()]}"
                        )

                    # Check if the directory exists
                    if not full_base_dir.exists() or not full_base_dir.is_dir():
                        logger.error(f"Directory not found: {full_base_dir}")
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"error": "Directory not found", "path": safe_base_dir}
                            ).encode()
                        )
                        return

                    # Load all requested files
                    result = {"files": {}, "errors": {}}

                    logger.info(f"Attempting to load {len(filenames)} files")

                    for filename in filenames:
                        # Sanitize filename to prevent directory traversal
                        safe_filename = os.path.basename(filename)
                        full_path = full_base_dir / safe_filename

                        logger.debug(f"Trying to read: {full_path}")

                        try:
                            if full_path.exists() and full_path.is_file():
                                # Read file content
                                with open(full_path, "r") as f:
                                    try:
                                        # Try to parse as JSON
                                        content = json.load(f)

                                        # Special handling for metadata.json files
                                        if safe_filename.lower() == "metadata.json":
                                            # Check and log timestamp format
                                            if content.get("experiment") and content[
                                                "experiment"
                                            ].get("timestamp"):
                                                timestamp = content["experiment"][
                                                    "timestamp"
                                                ]
                                                logger.info(
                                                    f"Metadata timestamp format in {full_path}: {timestamp} (type: {type(timestamp).__name__})"
                                                )

                                        result["files"][safe_filename] = content
                                        logger.debug(
                                            f"Successfully loaded file: {safe_filename}"
                                        )
                                    except json.JSONDecodeError as json_err:
                                        # Log detailed error info for metadata.json files
                                        if safe_filename.lower() == "metadata.json":
                                            logger.error(
                                                f"JSON decode error in {full_path}: {json_err}"
                                            )
                                            # Try to read the raw content for inspection
                                            f.seek(0)
                                            raw_content = f.read()
                                            logger.error(
                                                f"Raw content of problematic metadata.json: {raw_content[:200]}..."
                                            )

                                        # If not valid JSON, read as text
                                        f.seek(0)
                                        text_content = f.read()
                                        result["files"][safe_filename] = {
                                            "_raw_text": text_content
                                        }
                                        logger.debug(
                                            f"Loaded as raw text: {safe_filename}"
                                        )
                            else:
                                logger.warning(f"File not found: {full_path}")
                                result["errors"][safe_filename] = "File not found"
                        except Exception as e:
                            logger.error(f"Error reading file {full_path}: {e}")
                            result["errors"][safe_filename] = str(e)

                    # Log summary
                    logger.info(
                        f"Batch loading complete. Loaded {len(result['files'])} files, {len(result['errors'])} errors"
                    )

                    # Return the results
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                    return
                except Exception as e:
                    logger.error(f"Error processing batch file request: {e}")
                    import traceback

                    logger.error(traceback.format_exc())
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return

            # API endpoint to list files in an outputs directory
            elif self.path.startswith("/api/outputs-directory"):
                try:
                    # Parse the query parameter
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)
                    dir_path = params.get("path", [""])[0]

                    if not dir_path:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "path parameter is required"}).encode()
                        )
                        return

                    # Construct the full path to the directory
                    full_path = PARENT_DIR / dir_path.lstrip("/")
                    logger.info(f"Listing files in directory: {full_path}")

                    # Check if the directory exists
                    if not full_path.exists() or not full_path.is_dir():
                        logger.error(f"Directory not found: {full_path}")
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "Directory not found"}).encode()
                        )
                        return

                    # List all JSON files in the directory
                    files = [
                        f.name
                        for f in full_path.iterdir()
                        if f.is_file() and f.suffix == ".json"
                    ]
                    logger.info(f"Found {len(files)} JSON files in {full_path}")
                    logger.info(f"Files: {files}")

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"files": files}).encode())
                    return
                except Exception as e:
                    logger.error(f"Error listing directory: {e}")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    return

            # If not API request, handle as normal file request
            return super().do_GET()

        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

    def do_POST(self):
        # API endpoint for login
        if self.path == "/api/login":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(post_data)

                username = payload.get("username", "")
                password = payload.get("password", "")

                if username == AUTH_USERNAME and password == AUTH_PASSWORD:
                    # Generate a token
                    import hashlib
                    import hmac

                    token = hmac.new(
                        AUTH_TOKEN_SECRET.encode(),
                        f"{username}:{password}".encode(),
                        hashlib.sha256,
                    ).hexdigest()

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"success": True, "token": token}).encode()
                    )
                else:
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": "Invalid credentials"}).encode()
                    )

                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        # Check authentication for all other POST endpoints
        if not self.is_authenticated():
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Authentication required"}).encode())
            return

        # API endpoint to start a new process
        if self.path == "/api/process/start":
            if not self.is_authenticated():
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return

            # Check if experiment runner is disabled
            if DISABLE_EXPERIMENT_RUNNER:
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "Experiment runner is disabled"}).encode()
                )
                return

            try:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(post_data)

                command = payload.get("command", "")
                if not command:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"error": "Command is required"}).encode()
                    )
                    return

                # Create a new process ID
                process_id = str(uuid.uuid4())

                # Add initial log entry
                process_logs[process_id] = [
                    {
                        "timestamp": int(time.time()),
                        "message": f"Starting process: {command}",
                        "type": "info",
                    }
                ]

                # Create log file for this process
                log_file = LOG_DIR / f"process_{process_id}.log"
                try:
                    with open(log_file, "w") as f:
                        f.write(
                            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting process: {command}\n"
                        )
                except Exception as e:
                    logger.error(f"Error creating log file: {e}")

                try:
                    # Start the process
                    logger.info(f"Starting process: {command}")

                    # Create the subprocess environment
                    env = os.environ.copy()
                    # Disable output buffering for Python processes
                    env["PYTHONUNBUFFERED"] = "1"

                    # Use shell=True to enable shell features like redirection
                    process = subprocess.Popen(
                        command,  # Pass command as string instead of args list
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,  # Add stdin pipe for interactive processes
                        bufsize=0,  # Completely unbuffered
                        universal_newlines=False,
                        cwd=str(BASE_REPO_DIR),
                        env=env,
                        shell=True,  # Enable shell features like redirection
                    )

                    # Add process to active_processes
                    with process_lock:
                        active_processes[process_id] = {
                            "id": process_id,
                            "command": command,
                            "start_time": int(time.time()),
                            "status": "running",
                            "process": process,
                        }

                    # Start a thread to read process output
                    output_thread = threading.Thread(
                        target=read_process_output,
                        args=(process, process_id),
                        daemon=True,
                    )
                    output_thread.start()

                    # Send response with the new process ID
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"process_id": process_id}).encode())

                except Exception as e:
                    logger.error(f"Error starting process: {e}")

                    # Add error to logs
                    timestamp = int(time.time())
                    error_message = f"Failed to start process: {str(e)}"

                    with process_lock:
                        if process_id in process_logs:
                            process_logs[process_id].append(
                                {
                                    "timestamp": timestamp,
                                    "message": error_message,
                                    "type": "error",
                                }
                            )

                        # Mark process as failed
                        active_processes[process_id] = {
                            "id": process_id,
                            "command": command,
                            "start_time": int(time.time()),
                            "status": "failed",
                        }

                    # Log the error to the log file
                    try:
                        with open(log_file, "a") as f:
                            f.write(
                                f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] {error_message}\n"
                            )
                    except Exception as log_error:
                        logger.error(f"Error writing to log file: {log_error}")

                    # Return an error response
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": error_message}).encode())

                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        # API endpoint to stop a process
        elif self.path.startswith("/api/process/stop/"):
            if not self.is_authenticated():
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return

            # Check if experiment runner is disabled
            if DISABLE_EXPERIMENT_RUNNER:
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "Experiment runner is disabled"}).encode()
                )
                return

            try:
                # Extract process ID from the URL
                process_id = self.path.split("/")[-1]

                with process_lock:
                    if (
                        process_id in active_processes
                        and active_processes[process_id]["status"] == "running"
                    ):
                        process_info = active_processes[process_id]

                        # Terminate the process
                        if "process" in process_info:
                            process_info["process"].terminate()
                            logger.info(f"Terminated process: {process_id}")

                        # Update process status
                        active_processes[process_id]["status"] = "stopped"

                        # Add log entry
                        timestamp = int(time.time())
                        if process_id in process_logs:
                            process_logs[process_id].append(
                                {
                                    "timestamp": timestamp,
                                    "message": "Process stopped by user",
                                    "type": "warning",
                                }
                            )

                        # Log to file
                        log_file = LOG_DIR / f"process_{process_id}.log"
                        try:
                            with open(log_file, "a") as f:
                                f.write(
                                    f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] Process stopped by user\n"
                                )
                        except Exception as e:
                            logger.error(f"Error writing to log file: {e}")

                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True}).encode())
                    else:
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"error": "Process not found or not running"}
                            ).encode()
                        )
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        # API endpoint to send input to a running process
        elif self.path.startswith("/api/process/input/"):
            if not self.is_authenticated():
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
                return

            # Check if experiment runner is disabled
            if DISABLE_EXPERIMENT_RUNNER:
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "Experiment runner is disabled"}).encode()
                )
                return

            try:
                # Extract process ID from the URL
                process_id = self.path.split("/")[-1]

                # Read input data from request
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(post_data)

                input_text = payload.get("input", "")

                with process_lock:
                    if (
                        process_id in active_processes
                        and active_processes[process_id]["status"] == "running"
                        and "process" in active_processes[process_id]
                    ):
                        process_info = active_processes[process_id]
                        process = process_info["process"]

                        # Add input to log
                        timestamp = int(time.time())
                        if process_id in process_logs:
                            process_logs[process_id].append(
                                {
                                    "timestamp": timestamp,
                                    "message": f"User input: {input_text}",
                                    "type": "input",
                                }
                            )

                        # Log to file
                        log_file = LOG_DIR / f"process_{process_id}.log"
                        try:
                            with open(log_file, "a") as f:
                                f.write(
                                    f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] User input: {input_text}\n"
                                )
                        except Exception as e:
                            logger.error(f"Error writing to log file: {e}")

                        # Send input to process
                        try:
                            # Make sure input ends with newline
                            if not input_text.endswith("\n"):
                                input_text += "\n"

                            # Send to stdin
                            process.stdin.write(input_text.encode())
                            process.stdin.flush()

                            logger.info(
                                f"Sent input to process {process_id}: {input_text.strip()}"
                            )

                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(json.dumps({"success": True}).encode())
                        except Exception as e:
                            logger.error(f"Error sending input to process: {e}")
                            self.send_response(500)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(
                                json.dumps(
                                    {"error": f"Error sending input: {str(e)}"}
                                ).encode()
                            )
                    else:
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {"error": "Process not found or not running"}
                            ).encode()
                        )
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        # Handle other POST requests with a 404
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

    def do_OPTIONS(self):
        """Handle OPTIONS request"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, restart_event):
        self.restart_event = restart_event
        self.last_modified = time.time()

    def on_modified(self, event):
        # Avoid duplicate events by checking time
        current_time = time.time()
        if current_time - self.last_modified < 0.5:
            return
        self.last_modified = current_time

        # Check if it's a file we care about
        if not event.is_directory:
            path = Path(event.src_path)
            if path.suffix in [".html", ".css", ".js", ".json"]:
                logger.info(f"🔄 File changed: {path.name}")
                self.restart_event.set()


def start_server():
    global server
    handler = CustomHandler

    # Track restart attempts for backoff
    restart_attempts = 0
    max_restart_attempts = 5

    while True:
        try:
            # Reset the restart event
            restart_event.clear()

            # Configure socket to allow reuse
            socketserver.TCPServer.allow_reuse_address = True

            # Create and start the server
            server = socketserver.TCPServer(("", PORT), handler)
            logger.info(f"🌐 Server running at: http://localhost:{PORT}/")
            logger.info(f"📊 🔮 Large Language Oracle Results Analyzer")
            logger.info(f"📂 Serving files from: {PARENT_DIR}")
            logger.info("🔄 Auto-reload enabled (Ctrl+C to stop)")

            # Reset restart attempts on successful start
            restart_attempts = 0

            # Start the server in a separate thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            # Wait for the restart event
            restart_event.wait()

            # Shut down the server
            logger.info("🔄 Restarting server...")
            try:
                server.shutdown()
                server.server_close()
                # Add small delay to allow OS to fully release the socket
                time.sleep(0.5)
            except Exception as shutdown_error:
                logger.error(f"Error during shutdown: {shutdown_error}")
                # Force a longer delay if shutdown failed
                time.sleep(2)

        except KeyboardInterrupt:
            if server:
                try:
                    server.shutdown()
                    server.server_close()
                except Exception:
                    pass
            logger.info("👋 Server stopped")
            break
        except OSError as e:
            # Handle address already in use error specifically
            if e.errno == 48 or e.errno == 98:  # 48 on macOS, 98 on Linux
                restart_attempts += 1
                backoff_time = min(
                    1 * restart_attempts, 15
                )  # Exponential backoff, max 15 seconds

                logger.error(
                    f"❌ Address already in use (attempt {restart_attempts}/{max_restart_attempts})"
                )
                logger.info(f"Waiting {backoff_time} seconds before retry...")

                if restart_attempts >= max_restart_attempts:
                    logger.error(
                        "Maximum restart attempts reached. Trying to force kill existing process..."
                    )
                    try:
                        # Try to find and kill process using the port
                        kill_process_using_port(PORT)
                        # Reset counter after kill attempt
                        restart_attempts = 0
                        # Wait a bit longer after kill attempt
                        time.sleep(2)
                    except Exception as kill_error:
                        logger.error(f"Failed to kill process: {kill_error}")
                        time.sleep(5)
                else:
                    time.sleep(backoff_time)
            else:
                # Other OS errors
                logger.error(f"❌ Server error: {e}")
                time.sleep(2)
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            time.sleep(2)  # Longer wait time for general errors


# Helper function to find and kill a process using a specific port
def kill_process_using_port(port):
    """Find and kill process using the specified port"""
    try:
        if sys.platform.startswith("darwin"):  # macOS
            cmd = f"lsof -i :{port} -sTCP:LISTEN -t"
            pid = subprocess.check_output(cmd, shell=True).decode().strip()
            if pid:
                logger.info(
                    f"Found process {pid} using port {port}, attempting to terminate..."
                )
                subprocess.call(f"kill -9 {pid}", shell=True)
                return True
        elif sys.platform.startswith("linux"):  # Linux
            cmd = f"fuser -k {port}/tcp"
            subprocess.call(cmd, shell=True)
            return True
        elif sys.platform.startswith("win"):  # Windows
            cmd = f"FOR /F \"tokens=5\" %P IN ('netstat -ano ^| findstr :{port} ^| findstr LISTENING') DO taskkill /F /PID %P"
            subprocess.call(cmd, shell=True)
            return True
        return False
    except Exception as e:
        logger.error(f"Error finding or killing process: {e}")
        return False


def setup_file_watcher():
    global observer

    # Create and start the file observer
    observer = Observer()
    event_handler = FileChangeHandler(restart_event)

    try:
        # Watch UI directory
        logger.info(f"Setting up watcher for UI directory: {UI_DIR}")
        observer.schedule(event_handler, str(UI_DIR), recursive=False)

        # Watch outputs and reruns directories
        logger.info(f"Setting up watcher for outputs directory: {OUTPUTS_DIR}")
        observer.schedule(event_handler, str(OUTPUTS_DIR), recursive=False)

        logger.info(f"Setting up watcher for reruns directory: {RERUNS_DIR}")
        observer.schedule(event_handler, str(RERUNS_DIR), recursive=False)

        observer.start()
        logger.info("File watchers started successfully")
    except OSError as e:
        logger.error(
            f"Error setting up file watchers: {e}. Auto-reload will be disabled."
        )
        # Create a dummy observer if the real one fails
        observer = DummyObserver()

    return observer


# A dummy observer for when the real one can't be created
class DummyObserver:
    """A dummy observer that does nothing."""

    def stop(self):
        pass

    def join(self):
        pass


def run_server():
    # Open browser
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()

    try:
        # Set up file watcher
        observer = setup_file_watcher()

        # Start the server
        start_server()
    except KeyboardInterrupt:
        logger.info("👋 Stopping server...")
    finally:
        # Clean up the observer
        if observer:
            observer.stop()
            observer.join()

        # Terminate any running processes
        with process_lock:
            for process_id, process_info in active_processes.items():
                if process_info["status"] == "running" and "process" in process_info:
                    try:
                        process_info["process"].terminate()
                        logger.info(f"Terminated process: {process_id}")
                    except Exception as e:
                        logger.error(f"Error terminating process {process_id}: {e}")


if __name__ == "__main__":
    run_server()
