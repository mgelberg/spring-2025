📚 Project Overview
This project automates the export and parsing of historical performance data from Apple Music for Artists, including plays, listeners, and (optionally) other metrics like Shazams.

The system is modular, resumable, and extensible for multiple measures.

🏗️ System Components

Script	Purpose
config.py	Centralized static config (artist ID, output templates, song list)
get-webdriver.py	Logs in to Apple Music for Artists, scrapes page source HTML files for all songs, weeks, and measures
parse-page-data.py	Parses saved HTML into clean CSV files
run-export.py	Orchestrates scraping and parsing for the full dataset
⚙️ Configuration (Static Imports)
These settings are imported because they should remain constant across runs:

artist_id

output_html_file_template

output_csv_file_template

songs_to_scrape

sortKey, sortOrder, zoom

group_by

✅ Centralized control
✅ No need to pass these dynamically each time

🚀 Dynamic Settings (Passed via CLI)
These settings are passed as CLI arguments because they change per run:

week

song_id

group_by

measure

--force (overwrite protection)

✅ Maximum flexibility
✅ Script can adapt to different runs without editing code

🔁 How the System Works
Scraping

get-webdriver.py automatically loops over:

All songs in songs_to_scrape

All valid weeks after release date

All measures in measures

It saves page source files in html outputs/, named with {measure}, {week}, {song_id}, and {group_by}.

Parsing

run-export.py triggers parse-page-data.py for each song-week-measure combo.

parse-page-data.py extracts city-level data and saves it to parsed csvs/ folder.

Skips parsing if CSV already exists, unless --force is used.

🔑 Example Commands
Scraping all HTMLs:

bash
Copy
Edit
python get-webdriver.py
Parsing all data:

bash
Copy
Edit
python run-export.py
Parsing a single song manually (example):

bash
Copy
Edit
python parse-page-data.py 20250411 1807227251 city plays --force
📋 Project Structure
arduino
Copy
Edit
project-root/
├── html outputs/        # Scraped HTML files
├── parsed csvs/          # Parsed CSV files
├── config.py
├── get-webdriver.py
├── parse-page-data.py
├── run-export.py
└── README.md             # (this document)
🧠 Design Best Practices
CLI args for dynamic settings: ensures flexibility without hardcoding.

Imports for static configuration: centralizes key constants.

Force flags: protect against accidental overwrites, but allow manual refreshes.

Directory structure enforced: html outputs/ and parsed csvs/ automatically created if missing.

Resumable scraping and parsing: system skips already completed files automatically.

✨ Future Extensions
Add new measures (e.g., Shazams, Impressions) by simply adding to measures = [...]

Support scraping new grouping types (country, source, etc.)

Build velocity models and city-based heatmaps from parsed data

✅ Last Updated: August 2025
