#!/usr/bin/env python3

import os
import json
import datetime
from pathlib import Path


def create_experiment():
    """
    Create a new experiment directory with the required structure:
    - A directory named in the format 'ddmmyyyy-experiment-name'
    - A metadata.json file with user-supplied fields
    - An empty outputs directory
    """
    # Get the current date for the folder name
    today = datetime.datetime.now()
    date_prefix = today.strftime("%d%m%Y")
    timestamp = today.strftime("%H:%M %d-%m-%Y")

    # Prompt user for experiment details
    print("Creating a new experiment...")
    experiment_name = input(
        "Enter experiment name (will be added after the date in folder name): "
    )

    # Create directory name
    dir_name = f"{date_prefix}-{experiment_name.replace(' ', '-').lower()}"

    # Get the base results path
    script_dir = Path(__file__).parent
    results_dir = script_dir / "results"

    # Ensure results directory exists
    results_dir.mkdir(exist_ok=True)

    # Create the experiment directory
    experiment_dir = results_dir / dir_name
    if experiment_dir.exists():
        overwrite = input(
            f"Directory {experiment_dir} already exists. Overwrite? (y/n): "
        )
        if overwrite.lower() != "y":
            print("Aborting.")
            return

    experiment_dir.mkdir(exist_ok=True)

    # Create the outputs directory
    outputs_dir = experiment_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Prompt for metadata fields
    title = input("Enter experiment title: ")
    goal = input("Enter experiment goal: ")
    previous_experiment = input("Enter previous experiment (leave blank if none): ")

    # For modifications, allow multiple entries
    modifications = {}
    print("Enter modifications (leave both blank to finish):")
    while True:
        mod_key = input("Modification key (e.g., 'market_resolution_delay'): ")
        if not mod_key:
            break
        mod_value = input(f"Value for {mod_key}: ")
        modifications[mod_key] = mod_value

    # Create metadata dictionary
    metadata = {
        "experiment": {
            "timestamp": timestamp,
            "title": title,
            "goal": goal,
            "previous_experiment": previous_experiment if previous_experiment else None,
            "modifications": modifications,
            "system_prompt": None,
            "setup": None,
        }
    }

    # Write metadata to file
    metadata_path = experiment_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nExperiment created successfully at: {experiment_dir}")
    print("Remember to define system_prompt and setup when running the experiment.")


if __name__ == "__main__":
    create_experiment()
