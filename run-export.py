import subprocess
import argparse
import sys
import os
from config import (
    songs_to_scrape,
    group_by,
    get_valid_weeks_for_song,
    raw_week_endings,
    raw_month_starts,
    get_file_path,
    build_scrape_url,
    start_logged_in_browser,
    scrape_file,
    print_progress,
    build_pending_scrapes,
    print_scraping_plan,
    get_existing_parsed_files
)
import time

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force overwrite all outputs")
    parser.add_argument("--log-urls", action="store_true", default=False, help="Log URLs being requested")
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
        # Use Popen with all streams connected to terminal
        process = subprocess.Popen(
            cmd,
            stdout=None,  # Use None to connect to terminal
            stderr=None,  # Use None to connect to terminal
            stdin=None,   # Use None to connect to terminal
            universal_newlines=True
        )
        
        # Wait for the process to complete
        return_code = process.wait()
        
        if return_code != 0:
            print(f"❌ Error in {step_name}:")
            print(f"   Command: {' '.join(cmd)}")
            print(f"   Exit code: {return_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error in {step_name}:")
        print(f"   {str(e)}")
        return False

def main():
    args = parse_args()
    
    # Get user choices
    data_type, measure_choice, level_choice = get_user_choices()
    
    # Set measures and levels
    measures = ["listeners"] if measure_choice == 'l' else ["plays"] if measure_choice == 'p' else ["listeners", "plays"]
    levels = ["song"] if level_choice == 's' else ["artist"] if level_choice == 'a' else ["song", "artist"]
    
    # Add feedback about choices
    print(f"\n📋 Selected options:")
    print(f"   Period: {'Monthly' if data_type == 'm' else 'Weekly'}")
    print(f"   Measures: {', '.join(measures)}")
    print(f"   Levels: {', '.join(levels)}")
    if args.log_urls:
        print(f"   Logging URLs: Enabled")

    # Print scraping plan
    print_scraping_plan(level_choice, data_type)

    # Build pending scrapes list
    pending_scrapes = build_pending_scrapes(measures, levels, data_type, args.force)

    if not pending_scrapes:
        print("✅ No new HTML files to scrape. Everything is already up to date.")
    else:
        # Start browser and scrape
        first_scrape = pending_scrapes[0]
        first_url = build_scrape_url(
            first_scrape[2],
            first_scrape[1]["id"] if first_scrape[0] == "song" else None,
            measure=first_scrape[4],
            period_type="monthly" if data_type == 'm' else "weekly",
            log_urls=args.log_urls
        )
        driver = start_logged_in_browser(first_url)
        
        # Scrape files
        start_time = time.time()
        for i, (level, song_obj, period_value, html_file, measure) in enumerate(pending_scrapes):
            url = build_scrape_url(
                period_value,
                song_obj["id"] if song_obj else None,
                measure=measure,
                period_type="monthly" if data_type == 'm' else "weekly",
                log_urls=args.log_urls
            )
            
            current_song_name = song_obj["name"] if song_obj else None
            
            scrape_file(
                driver, 
                url, 
                html_file, 
                level=level,
                measure=measure,
                period_type="monthly" if data_type == 'm' else "weekly",
                period_value=period_value,
                song_name=current_song_name,
                log_urls=args.log_urls
            )
            print_progress(i, len(pending_scrapes), start_time)
        
        driver.quit()
        print("\n🎉 All scraping complete.")

    # Parse files
    parse_success = True
    existing_parsed_files = get_existing_parsed_files()  # Get set of already parsed files
    
    for measure in measures:
        for level in levels:
            if level == "artist":
                periods = raw_month_starts if data_type == 'm' else raw_week_endings
                for period in periods:
                    file_key = (
                        "monthly" if data_type == 'm' else "weekly",
                        measure,
                        group_by,
                        "artist",
                        period
                    )
                    if file_key in existing_parsed_files and not args.force:
                        continue
                        
                    cmd = ["python", "parse-page-data.py",
                           period,
                           "artist",
                           group_by,
                           "monthly" if data_type == 'm' else "weekly",
                           level,
                           "--measures", measure,
                           "--levels", level]
                    if args.force:
                        cmd.append("--force")
                    
                    if not run_command(cmd, f"Parsing {level} level data for {period}"):
                        parse_success = False
                        print(f"⚠️  Continuing with next file...")
            else:
                for song in songs_to_scrape:
                    song_id = song["id"]
                    periods = raw_month_starts if data_type == 'm' else get_valid_weeks_for_song(song)
                    for period in periods:
                        file_key = (
                            "monthly" if data_type == 'm' else "weekly",
                            measure,
                            group_by,
                            song_id,
                            period
                        )
                        if file_key in existing_parsed_files and not args.force:
                            continue
                            
                        cmd = ["python", "parse-page-data.py",
                               period,
                               song_id,
                               group_by,
                               "monthly" if data_type == 'm' else "weekly",
                               level,
                               "--measures", measure,
                               "--levels", level]
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