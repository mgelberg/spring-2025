# 🎧 Apple Music for Artists Scraping System

Automate the export and parsing of granular Apple Music for Artists data, including plays, listeners, and more — by song, city, and time period.

## ✨ Features

- ⏱️ Time-aware (won't scrape pre-release data)
- 📂 Organized (HTML and CSV outputs in separate folders)
- 🧠 Smart (skips existing files unless forced)
- 🧰 Extensible (multi-measure and multi-grouping ready)
- 🔍 Debug-friendly (optional URL logging)
- 📊 Data-driven (organized data storage)
- 🔄 Efficient (skips existing files with data)
- 🛠️ Modular (core logic centralized in config.py)

## 🏗️ Project Structure

    project-root/
    ├── data/                    # All CSV data files
    ├── html outputs/           # Scraped raw HTML pages
    ├── parsed csvs/            # Parsed data exports
    ├── config.py               # Core configuration and scraping logic
    ├── get-monthly-streams-apple.py  # Monthly data scraping
    ├── get-weekly-streams-apple.py   # Weekly data scraping
    ├── parse-page-data.py      # HTML to CSV parsing
    ├── run-export.py           # Main execution script
    ├── check-status.py         # Status checking
    ├── analyze_data.py         # Data analysis
    ├── build-song-velocity.py  # Song velocity calculations
    ├── get-song-ids.py         # Song ID retrieval
    ├── list_folders.py         # Directory management
    ├── requirements.txt        # Dependencies
    └── README.md              # Documentation

## ⚙️ Configuration

All static project-wide settings are centralized in `config.py`:

- Artist and song configurations
- Measurement types
- Output templates
- Grouping and sorting preferences
- Date calculation logic
- Core scraping functionality
- File management utilities

## 🚀 Usage

### Basic Scraping

```bash
# Weekly data
python get-weekly-streams-apple.py

# Monthly data
python get-monthly-streams-apple.py

# Parse data into CSVs
python run-export.py
```

### Advanced Options

```bash
# Force re-scrape existing files
python get-weekly-streams-apple.py --force

# Enable URL logging for debugging
python get-monthly-streams-apple.py --log-urls

# Parse specific file
python parse-page-data.py [date] [song_id] [grouping] [measure] --force
```

## 🛠️ Development

### Adding New Metrics
Edit `config.py`:
```python
measures = ["plays", "listeners", "shazams", "impressions"]
```

### Changing Groupings
Modify in `config.py`:
```python
group_by = "city"  # or "country", "source", etc.
```

## �� Troubleshooting

- **Login Issues**: Script will pause for manual login if needed
- **Empty CSVs**: Check for HTML structure changes in Apple's frontend
- **Debug Mode**: Use `--log-urls` flag to see requested URLs
- **Force Mode**: Use `--force` to re-scrape/parse existing files
- **File Skipping**: System automatically skips existing files with data
- **Error Recovery**: Improved error handling and logging

## 📊 Data Organization

- Raw HTML files are stored in `html outputs/`
- Parsed CSV files are stored in `parsed csvs/`
- All data files are organized in `data/` directory
- Each export maintains consistent naming conventions

## 🔄 Workflow

1. Configure settings in `config.py`
2. Run scraping scripts for desired time periods
3. Parse data using `run-export.py`
4. Analyze results using provided utility scripts

## 🔧 Recent Improvements

- Centralized scraping logic in `config.py`
- Optimized file checking and skipping
- Enhanced debugging capabilities
- Improved error handling
- Better organization of output files
- Streamlined scraping process