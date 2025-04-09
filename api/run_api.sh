#!/bin/bash

# Run the LLM Oracle API

# Check if virtual environment exists
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
else
    echo "Virtual environment not found. Installing requirements..."
    pip install -r requirements.txt
fi

# Run the API
echo "Starting LLM Oracle API..."
python main.py 