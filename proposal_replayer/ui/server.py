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

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Configuration
PORT = 8000
PARENT_DIR = Path(__file__).parent.parent
UI_DIR = PARENT_DIR / "ui"
RESULTS_DIR = PARENT_DIR / "results"
LOG_DIR = PARENT_DIR / "logs"
OUTPUTS_DIR = PARENT_DIR / "outputs"
RERUNS_DIR = PARENT_DIR / "reruns"
# Base repository directory (one level up from proposal_replayer)
BASE_REPO_DIR = PARENT_DIR.parent

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

                # Process complete lines
                lines = buffer.split(b"\n")
                # Last element may be a partial line
                if pipe == process.stdout:
                    stdout_buffer = lines[-1]
                    lines = lines[:-1]
                else:
                    stderr_buffer = lines[-1]
                    lines = lines[:-1]

                # Process each complete line
                for line in lines:
                    if not line:  # Skip empty lines
                        continue

                    line_str = line.decode("utf-8", errors="replace").rstrip()
                    timestamp = int(time.time())
                    log_type = "info" if pipe == process.stdout else "error"

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

            except (IOError, OSError) as e:
                # Handle pipe errors (e.g., when process terminates during read)
                if e.errno != errno.EAGAIN:
                    logger.error(f"Error reading from pipe: {e}")

        # Small sleep to prevent CPU spinning
        time.sleep(0.01)

    # Process has ended, handle any remaining data in buffers
    for buffer, pipe, log_type in [
        (stdout_buffer, process.stdout, "info"),
        (stderr_buffer, process.stderr, "error"),
    ]:
        if buffer:
            line_str = buffer.decode("utf-8", errors="replace").rstrip()
            if line_str:
                timestamp = int(time.time())
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
                except Exception as e:
                    logger.error(f"Error writing to log file: {e}")

    # Try to get any remaining stderr data
    try:
        stderr_data = process.stderr.read()
        if stderr_data:
            stderr_str = stderr_data.decode("utf-8", errors="replace").rstrip()
            if stderr_str:
                timestamp = int(time.time())
                log_entry = {
                    "timestamp": timestamp,
                    "message": stderr_str,
                    "type": "error",
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
                            f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {stderr_str}\n"
                        )
                except Exception as e:
                    logger.error(f"Error writing to log file: {e}")
    except:
        pass

    # Update process status
    exit_code = process.poll()
    with process_lock:
        if (
            process_id in active_processes
            and active_processes[process_id]["status"] == "running"
        ):
            active_processes[process_id]["status"] = (
                "completed" if exit_code == 0 else "failed"
            )

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

            # Write final status to log file
            log_file = LOG_DIR / f"process_{process_id}.log"
            try:
                with open(log_file, "a") as f:
                    f.write(
                        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {log_entry['message']}\n"
                    )
            except Exception as e:
                logger.error(f"Error writing to log file: {e}")

            logger.info(f"Process {process_id} {status_message}")


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
        super().__init__(*args, directory=str(PARENT_DIR), **kwargs)

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

    def do_GET(self):
        # API endpoint for results directories
        if self.path == "/api/results-directories":
            try:
                results = []
                for dir_path in RESULTS_DIR.iterdir():
                    if dir_path.is_dir():
                        metadata_file = dir_path / "metadata.json"
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
                                "goal": metadata.get("experiment", {}).get("goal", ""),
                                "metadata": metadata,
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
                                }
                            )

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())
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

        # API endpoint for active processes
        elif self.path == "/api/processes":
            try:
                # Convert process data to JSON-serializable format
                process_list = []
                with process_lock:
                    for pid, process in active_processes.items():
                        if pid in process_logs:
                            process_logs_data = process_logs[pid]
                        else:
                            process_logs_data = []

                        process_list.append(
                            {
                                "id": pid,
                                "command": process.get("command", ""),
                                "start_time": process.get("start_time", 0),
                                "status": process.get("status", "unknown"),
                                "logs": process_logs_data,
                            }
                        )

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(process_list).encode())
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        # API endpoint for specific process logs
        elif self.path.startswith("/api/process/"):
            try:
                # Extract process ID from the URL
                process_id = self.path.split("/")[-1]

                with process_lock:
                    if process_id in active_processes:
                        process_data = {
                            "id": process_id,
                            "command": active_processes[process_id].get("command", ""),
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
                    else:
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({"error": "Process not found"}).encode()
                        )
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        # If not API request, handle as normal file request
        return super().do_GET()

    def do_POST(self):
        # API endpoint to start a new process
        if self.path == "/api/process/start":
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

                    # Parse the command into arguments
                    args = shlex.split(command)

                    # Create the subprocess
                    env = os.environ.copy()
                    # Disable output buffering for Python processes
                    env["PYTHONUNBUFFERED"] = "1"

                    process = subprocess.Popen(
                        args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        bufsize=0,  # Completely unbuffered
                        universal_newlines=False,
                        cwd=str(BASE_REPO_DIR),
                        env=env,
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

        # Handle other POST requests with a 404
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())


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

    while True:
        try:
            # Reset the restart event
            restart_event.clear()

            # Create and start the server
            server = socketserver.TCPServer(("", PORT), handler)
            logger.info(f"🌐 Server running at: http://localhost:{PORT}/ui/")
            logger.info(f"📊 Large Language Oracle Results Analyzer")
            logger.info(f"📂 Serving files from: {PARENT_DIR}")
            logger.info("🔄 Auto-reload enabled (Ctrl+C to stop)")

            # Start the server in a separate thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            # Wait for the restart event
            restart_event.wait()

            # Shut down the server
            logger.info("🔄 Restarting server...")
            server.shutdown()
            server.server_close()

        except KeyboardInterrupt:
            if server:
                server.shutdown()
                server.server_close()
            logger.info("👋 Server stopped")
            break
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            time.sleep(1)  # Wait a bit before restarting


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
    threading.Timer(
        1.0, lambda: webbrowser.open(f"http://localhost:{PORT}/ui/")
    ).start()

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
