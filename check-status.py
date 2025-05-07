import os
import pandas as pd
import argparse
from config import (
    songs_to_scrape,
    measures,
    group_by,
    get_valid_weeks_for_song,
    output_html_file_template,
    output_csv_file_template
)

def check_status(export_csv=False):
    html_missing = []
    csv_missing = []
    csv_empty = []

    for measure in measures:
        for song in songs_to_scrape:
            song_id = song["id"]
            song_name = song["name"]
            valid_weeks = get_valid_weeks_for_song(song)

            for week in valid_weeks:
                html_path = output_html_file_template.format(
                    week=week, song_id=song_id, group_by=group_by, measure=measure
                )
                csv_path = output_csv_file_template.format(
                    week=week, song_id=song_id, group_by=group_by, measure=measure
                )

                if not os.path.exists(html_path):
                    html_missing.append((song_name, measure, week, "Missing HTML", html_path))
                if not os.path.exists(csv_path):
                    csv_missing.append((song_name, measure, week, "Missing CSV", csv_path))
                elif os.path.exists(csv_path):
                    try:
                        df = pd.read_csv(csv_path)
                        if df.empty:
                            csv_empty.append((song_name, measure, week, "Empty CSV", csv_path))
                    except Exception as e:
                        csv_empty.append((song_name, measure, week, f"Unreadable CSV ({e})", csv_path))

    all_issues = html_missing + csv_missing + csv_empty
    if all_issues:
        df = pd.DataFrame(
            all_issues,
            columns=["Song", "Measure", "Week", "Issue", "File Path"]
        )

        print("\n🔍 Missing or Empty Files:\n")
        print(df.to_string(index=False))

        if export_csv:
            df.to_csv("status-report.csv", index=False)
            print("\n📁 Exported report to status-report.csv")

    else:
        print("✅ All expected HTML and CSV files are present and non-empty.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="store_true", help="Export status results to CSV")
    args = parser.parse_args()

    check_status(export_csv=args.csv)
