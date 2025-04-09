#!/usr/bin/env python3

import os
import sys
from pathlib import Path

def list_folders(directory_path):
    try:
        # Get all items in the directory
        items = os.listdir(directory_path)
        
        # Filter for directories only
        folders = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
        
        # Sort folders alphabetically
        folders.sort()
        
        # Print header
        print("\nFolders in directory:")
        print("-" * 40)
        
        # Print each folder name in a column
        for folder in folders:
            print(folder)
            
        print("-" * 40)
        print(f"Total folders: {len(folders)}")
        
    except FileNotFoundError:
        print(f"Error: Directory {directory_path} not found")
    except PermissionError:
        print(f"Error: Permission denied to access {directory_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Get directory path from user input
    while True:
        directory = input("\nEnter the directory path (or press Enter for current directory): ").strip()
        if not directory:
            directory = "."
            break
        # Remove any surrounding quotes if present
        directory = directory.strip("'\"")
        if os.path.isdir(directory):
            break
        print(f"Error: {directory} is not a valid directory. Please try again.")
    
    list_folders(directory) 