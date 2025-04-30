# config.py
from datetime import datetime, timedelta
import os

# Base config for trends page
artist_id = "ami:identity:e6a35f7117e0ed7c0939675639157300"
measures = ["plays","listeners"]

sort_key = "total"
sort_order = "desc"
zoom = "d"
song_id = "1807227249"
group_by = "city"

# Output filename pattern
#output_html_file_template = "page_source_{week}_{song_id}_by_{group_by}.html"

output_html_file_template = "html outputs/page_source_{measure}_{week}_{song_id}_by_{group_by}.html"
output_csv_file_template = "parsed csvs/{measure}_by_{group_by}_{song_id}_{week}.csv"

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
    release_dt = datetime.strptime(song["release_date"], "%Y%m%d")
    return [w for w in raw_week_endings if datetime.strptime(w, "%Y%m%d") >= release_dt]

# --- 🔬 Optional Small-Batch Debugging Block ---

# You can safely uncomment this for quick test runs
# songs_to_scrape = [
#     {'name': 'That Thing', 'id': '1807227251', 'release_date': '20250401'},
#     {'name': 'Althea', 'id': '1748029276', 'release_date': '20240315'}
# ]
# raw_week_endings = ["20250411", "20250404"]
# measures = ["listeners"]