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
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

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

# Global variables
server = None
observer = None
restart_event = threading.Event()


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PARENT_DIR), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
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

        # If not API request, handle as normal file request
        return super().do_GET()


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

    # Watch UI directory
    observer.schedule(event_handler, str(UI_DIR), recursive=False)

    # Watch outputs and reruns directories
    observer.schedule(event_handler, str(PARENT_DIR / "outputs"), recursive=False)
    observer.schedule(event_handler, str(PARENT_DIR / "reruns"), recursive=False)

    observer.start()
    return observer


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


if __name__ == "__main__":
    run_server()
