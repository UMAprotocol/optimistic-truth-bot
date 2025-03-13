#!/usr/bin/env python3
"""
Simple HTTP server for the Large Language Oracle Results Analyzer
Usage: python server.py
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 8000
PARENT_DIR = Path(__file__).parent.parent
UI_DIR = PARENT_DIR / "ui"


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PARENT_DIR), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()


def run_server():
    handler = CustomHandler

    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"🌐 Server running at: http://localhost:{PORT}/ui/")
        print(f"📊 Large Language Oracle Results Analyzer")
        print(f"📂 Serving files from: {PARENT_DIR}")
        print("🔄 Press Ctrl+C to stop the server")

        # Open browser
        webbrowser.open(f"http://localhost:{PORT}/ui/")

        # Serve until process is killed
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
