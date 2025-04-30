# 🎧 Apple Music for Artists Scraping System

Automate the export and parsing of granular Apple Music for Artists data, including plays, listeners, and more — by song, city, and time period.

This modular scraping suite is:

- ⏱️ Time-aware (won’t scrape pre-release data)
- 📂 Organized (HTML and CSV outputs in separate folders)
- 🧠 Smart (skips existing files unless forced)
- 🧰 Extensible (multi-measure and multi-grouping ready)

---

## 🧱 Project Structure

project-root/ ├── html outputs/ # Scraped raw HTML pages ├── parsed csvs/ # Parsed data exports ├── config.py # Static project-wide settings ├── get-webdriver.py # Scrapes HTML data ├── parse-page-data.py # Parses HTML into CSV ├── run-export.py # Orchestrates scrape + parse └── README.md


---

## ⚙️ Configuration (via `config.py`)

Static project-wide settings like:

- `artist_id`
- `songs_to_scrape`: list of song names, IDs, and release dates
- `measures = ["plays", "listeners"]`
- `output_html_file_template` and `output_csv_file_template`
- `group_by`, `sort_key`, `sort_order`, `zoom`
- Week calculation logic based on last full Friday and release dates

You may enable a **debug mode** by uncommenting the "small batch" block near the bottom to test just a couple songs and weeks.

---

## 🚀 How to Use

### 1. Scrape all HTMLs (skips existing files unless forced)

```bash
python get-webdriver.py
```

To force re-scrape all pages, even if files already exist:

```python get-webdriver.py --force
```


3. Parse a single file manually (e.g. That Thing, listeners, Apr 11–17)
```bash
python parse-page-data.py 20250411 1807227251 city listeners --force
```
**✅ Force Mode: When and Why**
Use --force to:

Re-download already-saved HTML files

Re-parse and overwrite already-created CSV files

Debug a specific run without deleting files manually

If not used, the system will skip any work that’s already done.

**💡 Design Best Practices**

Principle	What we do
Dynamic values	Passed via CLI (e.g. week, measure, --force)
Static config	Centralized in config.py
Skipping logic	Files are skipped unless forced
Folder structure	Separate for HTML and CSVs
Multi-measure support	Loop over measures = [...]
Smart date logic	Scrapes only post-release
**🧠 Extend This System**
Want to add new metrics? Just edit:

```python
measures = ["plays", "listeners", "shazams", "impressions"]
```
Want to scrape new groupings (e.g. by country or source)? Change:

```python
group_by = "city"
```
**📊 Scraping Schedule Preview**
If you want to preview what will be scraped per run, uncomment this inside get-webdriver.py:

```python

print("📊 Scraping Schedule Overview:")
for song in songs_to_scrape:
    valid_weeks = get_valid_weeks_for_song(song)
    print(f"🎵 {song['name']} — {song['release_date']} — {len(valid_weeks)} weeks pulled")
```
**🧪 Troubleshooting**
Missing login? → The script pauses and asks you to log in manually once per session.

Getting empty CSVs? → Check if the HTML structure changed (Apple may have updated their frontend).

Debugging one-off? → Use parse-page-data.py directly on a single file.




