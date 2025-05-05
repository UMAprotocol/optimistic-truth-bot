#!/bin/bash

# Run the LLM Oracle API

# Function to check for pip/python command
check_command() {
    if command -v $1 &>/dev/null; then
        echo $1
        return 0
    fi
    return 1
}

# Determine Python command (python3 or python)
PYTHON_CMD=$(check_command python3 || check_command python)
if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python not found! Please install Python 3."
    exit 1
fi

# Determine pip command (pip3 or pip)
PIP_CMD=$(check_command pip3 || check_command pip)
if [ -z "$PIP_CMD" ]; then
    echo "Error: pip not found! Please install pip."
    exit 1
fi

# Check if virtual environment exists
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Installing requirements directly..."
    $PIP_CMD install -r requirements.txt
fi

# Create logs directory if it doesn't exist
mkdir -p ../logs

# Run the API with proper error handling
echo "Starting LLM Oracle API..."
$PYTHON_CMD main.py

# Check exit status
if [ $? -ne 0 ]; then
    echo "Error: API failed to start properly. Check logs for details."
    exit 1
fi