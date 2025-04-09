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
        print(f"Error: Directory '{directory_path}' not found")
    except PermissionError:
        print(f"Error: Permission denied to access '{directory_path}'")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Get directory path from command line argument or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    list_folders(directory) 