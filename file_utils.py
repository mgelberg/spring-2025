import os
from typing import Dict, Tuple, Optional

# File naming conventions
HTML_FILE_TEMPLATE = "html outputs/page_source_{period_type}_{measure}_by_{group_by}_{song_id}_{week}.html"
CSV_FILE_TEMPLATE = "parsed csvs/parsed_{period_type}_{measure}_by_{group_by}_{song_id}_{week}.csv"
ANALYSIS_OUTPUT_DIR = "analysis_outputs"

# File path components
PERIOD_TYPES = ["weekly", "monthly"]
MEASURES = ["plays", "listeners"]
GROUP_BY_OPTIONS = ["city"]  # Currently only city, but could expand
LEVELS = ["song", "artist"]

def get_file_path(
    period_type: str,
    measure: str,
    period_value: str,
    level: str,
    song_id: str,
    group_by: str
) -> str:
    """
    Generate the appropriate file path based on all parameters.
    
    Args:
        period_type: 'weekly' or 'monthly'
        measure: 'plays' or 'listeners'
        period_value: The week or month value (e.g. '20250425' for weekly)
        level: 'song' or 'artist'
        song_id: The song ID or 'artist' for artist level
        group_by: Currently only 'city'
        
    Returns:
        The full file path
    """
    if period_type not in PERIOD_TYPES:
        raise ValueError(f"period_type must be one of {PERIOD_TYPES}")
    if measure not in MEASURES:
        raise ValueError(f"measure must be one of {MEASURES}")
    if group_by not in GROUP_BY_OPTIONS:
        raise ValueError(f"group_by must be one of {GROUP_BY_OPTIONS}")
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}")
        
    return HTML_FILE_TEMPLATE.format(
        period_type=period_type,
        measure=measure,
        group_by=group_by,
        song_id=song_id,
        week=period_value
    )

def get_csv_path(
    period_type: str,
    measure: str,
    period_value: str,
    song_id: str,
    group_by: str
) -> str:
    """
    Generate the CSV file path for parsed data.
    
    Args:
        period_type: 'weekly' or 'monthly'
        measure: 'plays' or 'listeners'
        period_value: The week or month value
        song_id: The song ID or 'artist' for artist level
        group_by: Currently only 'city'
        
    Returns:
        The full CSV file path
    """
    return CSV_FILE_TEMPLATE.format(
        period_type=period_type,
        measure=measure,
        group_by=group_by,
        song_id=song_id,
        week=period_value
    )

def parse_filename(filename: str) -> Dict[str, str]:
    """
    Parse all components from a filename.
    
    Args:
        filename: The filename to parse
        
    Returns:
        Dictionary containing all parsed components:
        - period_type: 'weekly' or 'monthly'
        - measure: 'plays' or 'listeners'
        - group_by: Currently only 'city'
        - song_id: The song ID or 'artist'
        - week: The week or month value
    """
    parts = os.path.basename(filename).split("_")
    if len(parts) < 7:
        raise ValueError(f"Invalid filename format: {filename}")
        
    return {
        'period_type': parts[1],
        'measure': parts[2],
        'group_by': parts[4],
        'song_id': parts[5],
        'week': parts[6].replace('.csv', '')
    }

def should_process_file(
    file_path: str,
    existing_files: set,
    force: bool = False
) -> bool:
    """
    Check if a file should be processed based on existence and force flag.
    
    Args:
        file_path: Path to the file
        existing_files: Set of existing file keys
        force: Whether to force processing
        
    Returns:
        True if the file should be processed, False otherwise
    """
    # Always process if force flag is set
    if force:
        return True
        
    # Process if file doesn't exist
    if not os.path.exists(file_path):
        return True
        
    # Process if file exists but is empty or too small
    if os.path.getsize(file_path) <= 10:
        return True
        
    # Don't process if file exists and has content
    return False

def get_file_key(
    period_type: str,
    measure: str,
    group_by: str,
    song_id: str,
    week: str
) -> Tuple[str, str, str, str, str]:
    """
    Generate a unique key for a file to track its processing status.
    
    Args:
        period_type: 'weekly' or 'monthly'
        measure: 'plays' or 'listeners'
        group_by: Currently only 'city'
        song_id: The song ID or 'artist'
        week: The week or month value
        
    Returns:
        Tuple of (period_type, measure, group_by, song_id, week)
    """
    return (period_type, measure, group_by, song_id, week)

def ensure_directory_exists(file_path: str) -> None:
    """
    Ensure the directory for a file exists.
    
    Args:
        file_path: Path to the file
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True) 