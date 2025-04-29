import sys
import re
import pandas as pd
from bs4 import BeautifulSoup
from config import output_html_file_template, songs_to_scrape, measure, output_csv_file_template
import os

def parse_file(week, song_id, group_by):
    html_file = output_html_file_template.format(week=week, song_id=song_id, group_by=group_by)
    song_name = next((s["name"] for s in songs_to_scrape if s["id"] == song_id), "Unknown")

    # Load HTML and parse
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

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
                "Song ID": song_id
            })
            i += 4
    
    return pd.DataFrame(rows)

def main():
    if len(sys.argv) != 4:
        #print("❌ Usage: python3 parse-page-data.py <week_ending> <song_id> <group_by>")
        print("❌ Usage: python3 parse-page-data.py 20250404 1807227249 city")
        sys.exit(1)

    week = sys.argv[1]
    song_id = sys.argv[2]
    group_by = sys.argv[3]

    #df = pd.DataFrame(rows)
    df = parse_file(week, song_id, group_by) #gets dataframe directly
    csv_file = output_csv_file_template.format(
    week=week, song_id=song_id, group_by=group_by, measure=measure
    )
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    #outfile = f"{measure}_by_{group_by}_{song_id}_{week}.csv"
    df.to_csv(csv_file, index=False)
    print(f"✅ Parsed and saved: {outfile}")

if __name__ == "__main__":
    main()
