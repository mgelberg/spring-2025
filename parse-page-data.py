import sys
import re
import pandas as pd
from bs4 import BeautifulSoup
from config import (
    output_html_file_template,
    songs_to_scrape,
    output_csv_file_template,
    get_common_parser,
    get_song_id_for_level,
    get_file_path,
    get_existing_parsed_files
)
import argparse
import os

def parse_file(week, song_id, group_by, measure, period_type='weekly', level='song', force=False):
    # Get the appropriate song_id based on level
    file_song_id = get_song_id_for_level(level, song_id)
    
    # Use get_file_path to ensure consistency with scraping
    html_file = get_file_path(
        period_type=period_type,
        measure=measure,
        period_value=week,
        level=level,
        song_id=file_song_id,
        group_by=group_by
    )
    
    csv_file = output_csv_file_template.format(
        week=week, 
        song_id=file_song_id,
        group_by=group_by, 
        measure=measure, 
        period_type=period_type
    )

    # Only look up song name for song-level data
    song_name = "Artist Level" if level == "artist" else next((s["name"] for s in songs_to_scrape if s["id"] == song_id), "Unknown")

    # Load HTML and parse
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except FileNotFoundError:
        print(f"❌ Missing HTML source: {html_file}")
        return None
    
    text = soup.get_text(separator="\n", strip=True)
    lines = text.split("\n")

    # Look for city table
    start = None
    for i in range(len(lines)):
        if (
            lines[i] == "City" and
            lines[i + 1] == "Previous Period" and
            lines[i + 2] == "This Period" and
            lines[i + 3] == "Change"
        ):
            start = i + 4
            break

    rows = []
    if start is not None:
        i = start
        while i + 3 < len(lines):
            city = lines[i].strip()
            prev = lines[i + 1].strip().replace(',', '')
            curr = lines[i + 2].strip().replace(',', '')
            change = lines[i + 3].strip()

            if not prev.isdigit() or not curr.isdigit():
                break

            rows.append({
                "City": city,
                "Previous Period": int(prev),
                "Current Period": int(curr),
                "% Change": change,
                "Week": week,
                "Song": song_name,
                "Song ID": file_song_id,
                "Measure": measure,
                "Level": level
            })
            i += 4

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    df.to_csv(csv_file, index=False)
    print(f"✅ Parsed and saved: {csv_file}")
    return df

def parse_args():
    parser = get_common_parser()
    # Positional arguments first
    parser.add_argument("week", help="Week ending date")
    parser.add_argument("song_id", help="Apple Music Song ID")
    parser.add_argument("group_by", help="Group by dimension (e.g. city)")
    parser.add_argument("period_type", help="weekly or monthly")
    parser.add_argument("level", choices=["song", "artist"], help="Data level (song or artist)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Get the appropriate song_id based on level
    file_song_id = get_song_id_for_level(args.level, args.song_id)
    
    # Check if this file has already been parsed
    existing_files = get_existing_parsed_files()
    file_key = (args.period_type, args.measures[0], args.group_by, file_song_id, args.week)
    
    if file_key in existing_files and not args.force:
        print(f"🟡 Skipping (already parsed): {file_key}")
        return
    
    # Parse the specific file
    parse_file(
        args.week,
        args.song_id,
        args.group_by,
        args.measures[0],
        args.period_type,
        level=args.level,
        force=args.force
    )

if __name__ == "__main__":
    main()
