#!/usr/bin/env python3
"""
Simple script to delete result files with recommendations of p3 or p4.
Usage: python temp.py [results_directory]

If no results directory is provided, it will default to:
results/09042025-multi-operator-realtime-follower/outputs/
"""

import os
import sys
import json
import glob
from pathlib import Path

def delete_p3_p4_results(directory_path):
    """
    Delete result files containing p3 or p4 recommendations.
    
    Args:
        directory_path: Path to the directory containing result files
    
    Returns:
        tuple: (deleted_count, total_count)
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found: {directory_path}")
        return 0, 0
    
    # Get all JSON files in the directory
    result_files = glob.glob(os.path.join(directory_path, "result_*.json"))
    total_count = len(result_files)
    
    if total_count == 0:
        print(f"No result files found in {directory_path}")
        return 0, 0
    
    deleted_count = 0
    print(f"Scanning {total_count} result files...")
    
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Check recommendation
            recommendation = data.get('recommendation', '').lower()
            
            if recommendation in ['p3', 'p4']:
                print(f"Deleting {os.path.basename(file_path)} - recommendation: {recommendation}")
                os.remove(file_path)
                deleted_count += 1
                
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON in {file_path} - skipping")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return deleted_count, total_count

def main():
    # Default directory
    default_dir = "results/09042025-multi-operator-realtime-follower/outputs/"
    
    # Get directory from command line if provided
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
    else:
        directory_path = default_dir
        print(f"No directory specified, using default: {default_dir}")
    
    # Convert to absolute path
    abs_path = os.path.abspath(directory_path)
    print(f"Processing directory: {abs_path}")
    
    # Delete p3/p4 files
    deleted, total = delete_p3_p4_results(abs_path)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Total result files: {total}")
    print(f"Files deleted: {deleted}")
    print(f"Remaining files: {total - deleted}")

if __name__ == "__main__":
    main()