import subprocess
import argparse
import sys
from config import (
    songs_to_scrape
    , group_by
    , get_valid_weeks_for_song
    , generate_month_start_dates
    , measures as all_measures
)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force overwrite all outputs")
    return parser.parse_args()

def get_user_choices():
    """Get user input for data types and measures"""
    print("\n📊 Data Collection Options:")

    # Get date range info
    while True:
        data_type = input("1) What date ranges are you pulling? Enter m for monthly and w for weekly: ").lower()
        if data_type in ['m', 'w']:
            break
        print("Enter m for monthly and w for weekly")

    # Get measure types
    while True:
        measure_choice = input("2) Collect listeners, plays, or both? (l/p/b): ").lower()
        if measure_choice in ['l', 'p', 'b']:
            break
        print("Please enter l for listeners, p for plays, or b for both")

    # Get level type
    while True:
        level_choice = input("3) Collect song-level, artist-level, or both? (s/a/b): ").lower()
        if level_choice in ['s', 'a', 'b']:
            break
        print("Please enter s for song-level, a for artist-level, or b for both")

    return data_type, measure_choice, level_choice

def run_command(cmd, step_name):
    """Run a command and handle any errors"""
    try:
        print(f"\n🔁 {step_name}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {step_name}:")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Exit code: {e.returncode}")
        print(f"   Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in {step_name}:")
        print(f"   {str(e)}")
        return False

def main():
    args = parse_args()
    
    # Get user choices
    data_type, measure_choice, level_choice = get_user_choices()
    
    # Set measures based on user choice
    if measure_choice == 'l':
        measures = ["listeners"]
    elif measure_choice == 'p':
        measures = ["plays"]
    else:  # both
        measures = ["listeners", "plays"]
    
    # Set levels based on user choice
    if level_choice == 's':
        levels = ["song"]
    elif level_choice == 'a':
        levels = ["artist"]
    else:  # both
        levels = ["song", "artist"]
    
    # Add feedback about choices
    print(f"\n📋 Selected options:")
    print(f"   Period: {'Monthly' if data_type == 'm' else 'Weekly'}")
    print(f"   Measures: {', '.join(measures)}")
    print(f"   Levels: {', '.join(levels)}")

    # Step 1: Fetch HTML files
    if data_type == 'm':
        html_cmd = ["python", "get-monthly-streams-apple.py", "--measures"] + measures + ["--levels"] + levels
    else:
        html_cmd = ["python", "get-weekly-streams-apple.py", "--measures"] + measures + ["--levels"] + levels
    
    if args.force:
        html_cmd.append("--force")
    
    if not run_command(html_cmd, "Step 1: Fetch all HTML files"):
        print("❌ Failed to fetch HTML files. Exiting.")
        sys.exit(1)

    # Step 2: Parse files
    period_type = "monthly" if data_type == 'm' else "weekly"
    parse_success = True
    
    for measure in measures:
        for song in songs_to_scrape:
            song_id = song["id"]
            periods = generate_month_start_dates() if data_type == 'm' else get_valid_weeks_for_song(song)

            for period in periods:
                for level in levels:
                    cmd = ["python", "parse-page-data.py",
                           period,
                           song_id,
                           group_by,
                           measure,
                           period_type,
                           level]  # Add level parameter
                    if args.force:
                        cmd.append("--force")
                    
                    if not run_command(cmd, f"Parsing {level} level data for {song['name']} - {period}"):
                        parse_success = False
                        print(f"⚠️  Continuing with next file...")

    if parse_success:
        print("\n✅ All steps completed successfully!")
    else:
        print("\n⚠️  Completed with some errors. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()