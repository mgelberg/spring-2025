# config.py
from datetime import datetime, timedelta

# Week(s) to pull data for
weeks_back = 4

def get_last_full_7_days(reference_date=None):
    reference_date = reference_date or datetime.today()
    safe_reference = reference_date - timedelta(days=7)
    days_since_friday = (safe_reference.weekday() - 4) % 7
    return safe_reference - timedelta(days=days_since_friday)

latest_complete_friday = get_last_full_7_days()

week_endings = [
    (latest_complete_friday - timedelta(weeks=i)).strftime("%Y%m%d")
    for i in range(weeks_back)
]

# Songs to scrape (paste from earlier)
songs_to_scrape = [
    #{'name': 'Breaking Me Down', 'id': '1807227249'},
    {'name': 'That Thing', 'id': '1807227251'},
     {'name': 'Althea', 'id': '1748029276'}
    #,
    # {'name': 'What Home Is', 'id': '1711474234'},
    # {'name': 'The Way That It Was', 'id': '1711474242'},
    # {'name': 'Slipping Away', 'id': '1711474243'},
    # {'name': 'Crash', 'id': '1711474239'},
    # {'name': 'Kid', 'id': '1711474235'},
    # {'name': 'All In', 'id': '1711474237'},
    # {'name': 'Easy', 'id': '1711474241'},
    # {'name': 'Cycles', 'id': '1711474233'},
    # {'name': 'Holding On', 'id': '1711474240'}
]

# Base config for trends page
artist_id = "ami:identity:e6a35f7117e0ed7c0939675639157300"
sort_key = "total"
sort_order = "desc"
measure = "plays"
zoom = "d"
song_id = "1807227249"
group_by = "city"


# Output filename pattern
output_html_file_template = "page_source_{week}_{song_id}_by_{group_by}.html"