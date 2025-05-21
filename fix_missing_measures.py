import pandas as pd
import glob
import os

def extract_measure_from_filename(filename):
    # Example filename: parsed_weekly_plays_by_city_1711474233_20250425.csv
    parts = os.path.basename(filename).split("_")
    if len(parts) >= 3:
        return parts[2]  # plays or listeners
    return None

def fix_missing_measures():
    # Get all CSV files in the parsed csvs directory
    csv_files = glob.glob("parsed csvs/*.csv")
    files_fixed = 0
    files_with_issues = []
    
    for file in csv_files:
        try:
            # Read the CSV
            df = pd.read_csv(file)
            
            # Skip empty files
            if df.empty:
                continue
            
            # Convert all column names to lowercase for checking
            lowercase_columns = [col.lower() for col in df.columns]
            
            # Check if any form of measure column exists
            if 'measure' not in lowercase_columns and 'Measure' not in df.columns:
                measure = extract_measure_from_filename(file)
                if measure:
                    print(f"Adding Measure column to {file}")
                    df['Measure'] = measure
                    df.to_csv(file, index=False)
                    files_fixed += 1
                else:
                    files_with_issues.append(f"Could not extract measure from filename: {file}")
            else:
                # If we have both 'measure' and 'Measure', fix it
                if 'measure' in df.columns and 'Measure' not in df.columns:
                    print(f"Fixing case of measure column in {file}")
                    df = df.rename(columns={'measure': 'Measure'})
                    df.to_csv(file, index=False)
                    files_fixed += 1
                elif 'measure' in df.columns and 'Measure' in df.columns:
                    print(f"Removing duplicate measure column in {file}")
                    # Keep 'Measure' and drop 'measure'
                    df = df.drop(columns=['measure'])
                    df.to_csv(file, index=False)
                    files_fixed += 1
            
        except Exception as e:
            files_with_issues.append(f"Error processing {file}: {str(e)}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Files fixed: {files_fixed}")
    if files_with_issues:
        print("\nFiles with issues:")
        for issue in files_with_issues:
            print(f"- {issue}")

if __name__ == "__main__":
    fix_missing_measures() 