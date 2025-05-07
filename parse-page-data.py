import sys
import re
import pandas as pd
from bs4 import BeautifulSoup
from config import output_html_file_template, songs_to_scrape, output_csv_file_template
import argparse
import os

def parse_file(week, song_id, group_by, measure, period_type='weekly', force=False):
    csv_file = output_csv_file_template.format(
    week=week, song_id=song_id, group_by=group_by, measure=measure, period_type=period_type
    )

    if os.path.exists(csv_file) and not force:
        print(f"🟡 Skipping (already parsed): {csv_file}")
        return None
    
    html_file = output_html_file_template.format(week=week, song_id=song_id, group_by=group_by, measure=measure, period_type=period_type)
    song_name = next((s["name"] for s in songs_to_scrape if s["id"] == song_id), "Unknown")

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
            prev = lines[i + 1].strip()
            curr = lines[i + 2].strip()
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
                "Song ID": song_id,
                "Measure": measure
            })
            i += 4
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    df.to_csv(csv_file, index=False)
    print(f"✅ Parsed and saved: {csv_file}")
    return df

# MAIN entry point — CLI wrapper
def parse_args():  # NEW
    parser = argparse.ArgumentParser()
    parser.add_argument("week", help="Week ending date")
    parser.add_argument("song_id", help="Apple Music Song ID")
    parser.add_argument("group_by", help="Group by dimension (e.g. city)")
    parser.add_argument("measure", help="Measure (e.g. plays, listeners)")  # NEW
    parser.add_argument("--force", action="store_true", help="Force re-parse even if file exists")  # NEW
    parser.add_argument("period_type", help="weekly or monthly")
    return parser.parse_args()

def main():
    args = parse_args()  # NEW
    parse_file(args.week, args.song_id, args.group_by, args.measure, args.period_type, force=args.force)  # CHANGED

if __name__ == "__main__":
    main()
