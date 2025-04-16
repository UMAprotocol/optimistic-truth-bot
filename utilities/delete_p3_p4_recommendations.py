#!/usr/bin/env python3

import os
import json
import argparse
from glob import glob

def delete_p3_p4_recommendations(directory):
    """
    Delete all result files in the given directory that have a P3 or P4 recommendation.
    
    Args:
        directory (str): Path to the directory containing result files
    """
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return
    
    # Get all JSON files in the directory and subdirectories
    result_files = glob(os.path.join(directory, "**", "*.json"), recursive=True)
    
    deleted_count = 0
    error_count = 0
    p3_count = 0
    p4_count = 0
    
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    
                    # Check if the file has a recommendation field
                    recommendation = None
                    
                    # Check for recommendation in the result object
                    if "result" in data and "recommendation" in data["result"]:
                        recommendation = data["result"]["recommendation"].lower()
                    
                    # Check for recommendation in the root level
                    elif "recommendation" in data:
                        recommendation = data["recommendation"].lower()
                    
                    # Check in proposed_price_outcome
                    elif "proposed_price_outcome" in data:
                        recommendation = data["proposed_price_outcome"].lower()
                    
                    # If we found a P3 or P4 recommendation, delete the file
                    if recommendation in ["p3", "p4"]:
                        if recommendation == "p3":
                            p3_count += 1
                        else:
                            p4_count += 1
                            
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"Deleted: {file_path} (Recommendation: {recommendation})")
                        
                except json.JSONDecodeError:
                    error_count += 1
                    print(f"Error: {file_path} is not a valid JSON file")
                    
        except Exception as e:
            error_count += 1
            print(f"Error processing {file_path}: {str(e)}")
    
    print(f"\nSummary:")
    print(f"Total files deleted: {deleted_count}")
    print(f"P3 recommendations deleted: {p3_count}")
    print(f"P4 recommendations deleted: {p4_count}")
    print(f"Errors encountered: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete result files with P3 or P4 recommendations")
    parser.add_argument("directory", help="Directory containing result files")
    args = parser.parse_args()
    
    delete_p3_p4_recommendations(args.directory)