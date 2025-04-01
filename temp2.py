#!/usr/bin/env python3
import json
import os
import argparse
import glob

def fix_json_structure(file_path):
    """
    Fix the structure of the JSON file by moving fields at the proposal_metadata level
    to the top level of the JSON object.
    """
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not parse JSON in file {file_path}")
            return False
    
    # Fields to move from proposal_metadata to the top level
    fields_to_move = ['icon', 'end_date_iso', 'game_start_time', 'tags']
    
    if 'proposal_metadata' in data:
        for field in fields_to_move:
            if field in data['proposal_metadata'] and field not in data:
                # Move the field from proposal_metadata to top level
                data[field] = data['proposal_metadata'][field]
                
                # Optionally, remove from proposal_metadata
                # del data['proposal_metadata'][field]
    
    # Write the updated data back to the file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return True

def process_directory(directory_path):
    """
    Process all JSON files in the given directory.
    """
    pattern = os.path.join(directory_path, "**", "*.json")
    files = glob.glob(pattern, recursive=True)
    
    success_count = 0
    error_count = 0
    
    for file_path in files:
        print(f"Processing {file_path}...")
        if fix_json_structure(file_path):
            success_count += 1
        else:
            error_count += 1
    
    print(f"\nProcessing complete:")
    print(f"Successfully processed: {success_count} files")
    print(f"Failed to process: {error_count} files")

def main():
    parser = argparse.ArgumentParser(description='Fix JSON structure by moving fields from proposal_metadata to top level')
    parser.add_argument('directory', type=str, help='Directory containing JSON files to process')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    process_directory(args.directory)

if __name__ == "__main__":
    main()