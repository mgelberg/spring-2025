import pandas as pd
import os
import glob
from typing import List, Tuple, Optional

def extract_week_from_filename(filename: str) -> str:
    """
    Extract the week from a filename.
    
    Parameters:
    -----------
    filename : str
        The filename to extract from
        
    Returns:
    --------
    str
        The week extracted from the filename
    """
    parts = os.path.basename(filename).split("_")
    return parts[-1].replace(".csv", "")

def extract_song_id_from_filename(filename: str) -> str:
    """
    Extract the song ID from a filename.
    
    Parameters:
    -----------
    filename : str
        The filename to extract from
        
    Returns:
    --------
    str
        The song ID extracted from the filename
    """
    parts = os.path.basename(filename).split("_")
    return parts[-2].replace(".csv", "")

def extract_group_by_from_filename(filename: str) -> str:
    """
    Extract the group by value from a filename.
    
    Parameters:
    -----------
    filename : str
        The filename to extract from
        
    Returns:
    --------
    str
        The group by value extracted from the filename
    """
    parts = os.path.basename(filename).split("_")
    return parts[-3].replace(".csv", "")

def extract_measure_from_filename(filename: str) -> str:
    """
    Extract the measure from a filename.
    
    Parameters:
    -----------
    filename : str
        The filename to extract from
        
    Returns:
    --------
    str
        The measure extracted from the filename
    """
    parts = os.path.basename(filename).split("_")
    return parts[0]

def extract_period_type_from_filename(filename: str) -> str:
    """
    Extract the period type from a filename.
    
    Parameters:
    -----------
    filename : str
        The filename to extract from
        
    Returns:
    --------
    str
        The period type extracted from the filename
    """
    parts = os.path.basename(filename).split("_")
    return parts[1]

def load_all_csvs(data_dir: str = "parsed csvs") -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """
    Load and combine all CSV files from the specified directory.
    
    Parameters:
    -----------
    data_dir : str, default="parsed csvs"
        Directory containing the CSV files
        
    Returns:
    --------
    Tuple[pd.DataFrame, List[Tuple[str, str]]]
        A tuple containing:
        - DataFrame with all combined data
        - List of tuples (song_id, week) for empty files
        
    Raises:
    -------
    ValueError
        If no valid data files are found
    """
    all_files = glob.glob(os.path.join(data_dir, "*_by_*.csv"))
    dataframes = []
    empty_files = []
    
    for file in all_files:
        try:
            if os.path.getsize(file) <= 1:
                continue
                
            measure = extract_measure_from_filename(file)    
            week = extract_week_from_filename(file)
            song_id = extract_song_id_from_filename(file)
            group_by = extract_group_by_from_filename(file)
            period_type = extract_period_type_from_filename(file)
            
            df = pd.read_csv(file, index_col=None)
            if df.empty:
                empty_files.append((song_id, week))
                continue
            
            # If Level column is missing, infer it from the Song field
            if 'Level' not in df.columns:
                df['Level'] = df['Song'].apply(lambda x: 'artist' if x == 'Artist Level' else 'song')
            
            # Add metadata columns
            df['period_type'] = period_type
            df['grouping'] = group_by
            
            # Reset index to ensure no duplicate indices
            df = df.reset_index(drop=True)
            
            dataframes.append(df)
            
        except pd.errors.EmptyDataError:
            empty_files.append((song_id, week))
            continue
        except Exception as e:
            continue
    
    if empty_files:
        with open("empty_files_to_rescrape.txt", "w") as f:
            f.write("# Run these commands to re-scrape empty files:\n")
            for song_id, week in empty_files:
                command = f"python run-export.py --force {week} {song_id}\n"
                f.write(command)

    if not dataframes:
        raise ValueError("No valid data files were found!")
    
    # Combine all dataframes and ensure no duplicate indices
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    return combined_df, empty_files

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the DataFrame by standardizing column names and adding necessary columns.
    
    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame
        
    Returns:
    --------
    pd.DataFrame
        The prepared DataFrame
    """
    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace('-', '_')
    )
    
    return df

def load_and_prepare_data(data_dir: str = "parsed csvs", 
                         output_file: Optional[str] = "song_velocity_table.csv") -> pd.DataFrame:
    """
    Load all CSV files, prepare the data, and optionally save to a file.
    
    Parameters:
    -----------
    data_dir : str, default="parsed csvs"
        Directory containing the CSV files
    output_file : Optional[str], default="song_velocity_table.csv"
        If provided, save the prepared DataFrame to this file
        
    Returns:
    --------
    pd.DataFrame
        The prepared DataFrame
        
    Raises:
    -------
    ValueError
        If no valid data files are found
    """
    # Load all CSV files
    df, empty_files = load_all_csvs(data_dir)
    
    # Prepare the DataFrame
    df = prepare_dataframe(df)
    
    # Save to file if requested
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"✅ {output_file} created with prepared data")
    
    return df

if __name__ == "__main__":
    # Example usage
    df = load_and_prepare_data()
    print(f"\nLoaded data shape: {df.shape}")
    print("\nColumns:", df.columns.tolist())
    print("\nSample data:")
    print(df.head()) 