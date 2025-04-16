# config.py

artist_id = "ami:identity:e6a35f7117e0ed7c0939675639157300"
week_endings = ["20250404", "20250328"]  # current and previous weeks
measure = "plays"
group_by = "city"
sort_key = "total"
sort_order = "desc"
zoom = "d"

output_html_file_template = "page_source_{}.html"  # will use week_ending to fill