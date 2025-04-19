# config.py

# Week(s) to pull data for
week_endings = ["20250404", "20250328"]

# Songs to scrape (paste from earlier)
songs_to_scrape = [
    {'name': 'Breaking Me Down', 'id': '1807227249'},
    {'name': 'That Thing', 'id': '1807227251'}
    #,
    # {'name': 'Althea', 'id': '1748029276'},
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