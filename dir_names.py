import os

def list_folders_in_directory(directory_path):
    try:
        # Get all entries in the directory
        entries = os.listdir(directory_path)
        
        # Filter out only directories
        folders = [entry for entry in entries if os.path.isdir(os.path.join(directory_path, entry))]
        
        # Print the folder names in a tabular format
        print("Folders:")
        print("--------")
        for folder in folders:
            print(folder)
    
    except FileNotFoundError:
        print(f"The directory {directory_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Replace 'your_directory_path' with the path to the directory you want to list
list_folders_in_directory('/Volumes/USB DISK/_arbhar_scenes')