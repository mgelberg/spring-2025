# config.py
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import os
import argparse
import glob
import pandas as pd

# Base config for trends page
artist_id = "ami:identity:e6a35f7117e0ed7c0939675639157300"

sort_key = "total"
sort_order = "desc"
zoom = "d"
song_id = "1807227249"
group_by = "city"

def get_common_parser():
    """Get common argument parser for all scraping scripts"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force re-download HTML files")
    parser.add_argument("--measures", nargs="+", choices=["listeners", "plays"], required=True,
                       help="Which measures to scrape (listeners and/or plays)")
    parser.add_argument("--levels", nargs="+", choices=["song", "artist"], required=True,
                       help="Which levels to scrape (song and/or artist)")
    return parser

def build_scrape_url(period_value, song_id=None, measure=None, period_type="weekly", level="song", log_urls=False):
    """Build URL for scraping with proper period format"""
    if measure is None:
        raise ValueError("Measure is required")
    if period_type not in ["weekly", "monthly"]:
        raise ValueError("period_type must be 'weekly' or 'monthly'")
    if level not in ["song", "artist"]:
        raise ValueError("level must be 'song' or 'artist'")
    
    period_prefix = "m" if period_type == "monthly" else "w"
    period_value_for_url = period_value[:6] if period_type == "monthly" else period_value
    
    url = (
        f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
        f"?period={period_prefix}~{period_value_for_url}"
        f"&sortKey={sort_key}"
        f"&sortOrder={sort_order}"
        f"&measure={measure}"
        f"&zoom={zoom}"
        f"&groupBy={group_by}"
        f"&annotationsVisible=true"
    )
    
    if level == "song" and song_id:
        url += f"&filter=song~{song_id}"
    
    if log_urls:
        print(f"\n🔗 URL for {level} level scrape:")
        print(f"   {url}")
    
    return url

def start_logged_in_browser(url):
    """Start browser and wait for manual login"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    
    print(f"\n🔗 Navigating to login page...")
    print(f"   URL: {url}")
    driver.get(url)
    print("\n⚠️  ATTENTION: Please log in manually in the browser window")
    print("   Press ENTER after you have logged in...")
    input("   > ")
    print("✅ Login confirmed, continuing with scraping...")
    return driver

def scrape_file(driver, url, output_path):
    """Scrape single file and save HTML"""
    try:
        print(f"🌐 Requesting URL: {url}")
        driver.get(url)
        time.sleep(random.uniform(10, 19))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"✅ Saved HTML to {output_path}")
    except Exception as e:
        print(f"❌ Error scraping {url}: {str(e)}")
        raise

def print_progress(i, total, start_time):
    """Print progress with ETA"""
    elapsed = time.time() - start_time
    progress = i + 1
    eta = int((elapsed / progress) * (total - progress))
    print(
        f"📊 Progress: {progress}/{total} "
        f"({round(100 * progress / total)}%) "
        f"⏳ ETA: {eta // 60}m {eta % 60}s"
    )

# Output filename pattern

output_html_file_template = "html outputs/page_source_{period_type}_{measure}_by_{group_by}_{song_id}_{week}.html"  # CHANGED
output_csv_file_template  = "parsed csvs/parsed_{period_type}_{measure}_by_{group_by}_{song_id}_{week}.csv"  # CHANGED


# Songs to scrape (paste from earlier)
songs_to_scrape = [
    {'name': 'Breaking Me Down', 'id': '1807227249', 'release_date': '20250425'},
    {'name': 'That Thing', 'id': '1807227251', 'release_date': '20250321'},
    {'name': 'Althea', 'id': '1748029276', 'release_date': '20240621'},
    {'name': 'What Home Is', 'id': '1711474234', 'release_date': '20231110'},
    {'name': 'The Way That It Was', 'id': '1711474242', 'release_date': '20231110'},
    {'name': 'Slipping Away', 'id': '1711474243', 'release_date': '20231110'},
    {'name': 'Crash', 'id': '1711474239', 'release_date': '20231110'},
    {'name': 'Kid', 'id': '1711474235', 'release_date': '20231110'},
    {'name': 'All In', 'id': '1711474237', 'release_date': '20231110'},
    {'name': 'Easy', 'id': '1711474241', 'release_date': '20231110'},
    {'name': 'Cycles', 'id': '1711474233', 'release_date': '20231110'},
    {'name': 'Holding On', 'id': '1711474240', 'release_date': '20231110'}
]

def get_last_full_friday(reference_date=None):
    """Get the most recent Friday that begins a full 7-day Apple reporting period."""
    reference_date = reference_date or datetime.today()
    safe_reference = reference_date - timedelta(days=7)
    days_since_friday = (safe_reference.weekday() - 4) % 7
    return safe_reference - timedelta(days=days_since_friday)

#latest_complete_friday = get_last_full_7_days()
def generate_raw_week_ending():
    """List all week-ending Fridays from the earliest song release up to latest complete week."""
    latest_friday = get_last_full_friday()
    earliest_release = min(datetime.strptime(song["release_date"], "%Y%m%d") for song in songs_to_scrape)
    
    raw_weeks = []
    current = latest_friday
    while current >= earliest_release:
        raw_weeks.append(current.strftime("%Y%m%d"))
        current -= timedelta(weeks=1)

    return sorted(raw_weeks, reverse=True)


# All available weeks
raw_week_endings = generate_raw_week_ending()

# Utility: filter weeks to only include those on/after the song's release
def get_valid_weeks_for_song(song):
    """Get valid weeks for a song based on its release date."""
    release_dt = datetime.strptime(song["release_date"], "%Y%m%d")
    return [w for w in raw_week_endings if datetime.strptime(w, "%Y%m%d") >= release_dt]

# Generate 1st-of-month dates for fully completed months up to now
def generate_month_start_dates():
    """Generate 1st-of-month dates for fully completed months up to now."""
    latest = get_last_full_friday()
    
    # If we're in the first 7 days of the month, include the previous month
    if latest.day <= 7:
        current = datetime(latest.year, latest.month, 1)
    else:
        # Otherwise, start from the previous month
        if latest.month == 1:
            current = datetime(latest.year - 1, 12, 1)
        else:
            current = datetime(latest.year, latest.month - 1, 1)
    
    # Start from earliest release date
    earliest = min(datetime.strptime(song["release_date"], "%Y%m%d") for song in songs_to_scrape)
    earliest = datetime(earliest.year, earliest.month, 1)  # First of month
    
    dates = []
    while current >= earliest:
        dates.append(current.strftime("%Y%m01"))
        # Move to previous month
        if current.month == 1:
            current = datetime(current.year - 1, 12, 1)
        else:
            current = datetime(current.year, current.month - 1, 1)
    
    return sorted(dates, reverse=True)

raw_month_starts = generate_month_start_dates()


# --- 🔬 Optional Small-Batch Debugging Block ---

# You can safely uncomment this for quick test runs
# songs_to_scrape = [
#     {'name': 'Breaking Me Down', 'id': '1807227249', 'release_date': '20250425'},
#     {'name': 'That Thing', 'id': '1807227251', 'release_date': '20250321'}
# ]
# raw_week_endings = ["20250502", "20250425"]
# raw_month_starts = ["20250401", "20250301"]  # Add this line
# # measures = ["listeners"]
# ---- end small-batch debugging ---

def get_song_id_for_level(level, song_id):
    """Get the appropriate song_id value based on level"""
    if level == "artist":
        return "artist"
    return song_id

def get_file_path(period_type, measure, period_value, level, song_id, group_by):
    """Generate the appropriate file path based on all parameters"""
    return output_html_file_template.format(
        period_type=period_type,
        measure=measure,
        group_by=group_by,
        song_id=get_song_id_for_level(level, song_id),
        week=period_value
    )

def build_pending_scrapes(measures, levels, data_type, force=False):
    """Build list of files that need to be scraped"""
    pending_scrapes = []
    period_type = "monthly" if data_type == 'm' else "weekly"
    
    for measure in measures:
        for level in levels:
            if level == "artist":
                periods = raw_month_starts if data_type == 'm' else raw_week_endings
                for period in periods:
                    html_file = get_file_path(
                        period_type=period_type,
                        measure=measure,
                        period_value=period,
                        level=level,
                        song_id="artist",
                        group_by=group_by
                    )
                    if not os.path.exists(html_file) or force:
                        pending_scrapes.append((level, None, period, html_file, measure))
            else:
                for song in songs_to_scrape:
                    song_id = song["id"]
                    periods = raw_month_starts if data_type == 'm' else get_valid_weeks_for_song(song)
                    for period in periods:
                        html_file = get_file_path(
                            period_type=period_type,
                            measure=measure,
                            period_value=period,
                            level=level,
                            song_id=song_id,
                            group_by=group_by
                        )
                        if not os.path.exists(html_file) or force:
                            pending_scrapes.append((level, song, period, html_file, measure))
    return pending_scrapes

def print_scraping_plan(level_choice, data_type):
    """Print the scraping plan based on selected options"""
    print("\n📋 Scraping Plan:")
    if level_choice == 'a':
        periods = raw_month_starts if data_type == 'm' else raw_week_endings
        print(f" Artist Level — {len(periods)} periods to scrape")
    elif level_choice == 's':
        for song in songs_to_scrape:
            song_id = song["id"]
            periods = raw_month_starts if data_type == 'm' else get_valid_weeks_for_song(song)
            print(f" {song['name']} — {len(periods)} periods to scrape")
    else:  # both
        periods = raw_month_starts if data_type == 'm' else raw_week_endings
        print(f" Artist Level — {len(periods)} periods to scrape")
        for song in songs_to_scrape:
            song_id = song["id"]
            periods = raw_month_starts if data_type == 'm' else get_valid_weeks_for_song(song)
            print(f" {song['name']} — {len(periods)} periods to scrape")

def get_existing_parsed_files():
    """Get a set of already parsed files"""
    parsed_files = set()
    csv_pattern = "parsed csvs/parsed_*.csv"
    
    for csv_file in glob.glob(csv_pattern):
        # Extract the key components from the filename
        # Example: parsed_weekly_plays_by_city_1711474233_20250425.csv
        parts = os.path.basename(csv_file).replace('.csv', '').split('_')
        period_type = parts[1]
        measure = parts[2]
        group_by = parts[4]
        song_id = parts[5]
        week = parts[6]
        parsed_files.add((period_type, measure, group_by, song_id, week))
    
    return parsed_files