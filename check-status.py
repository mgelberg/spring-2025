import os
import pandas as pd
import argparse
from config import (
    songs_to_scrape,
    group_by,
    get_valid_weeks_for_song,
    raw_week_endings,
    raw_month_starts,
    output_html_file_template,
    output_csv_file_template,
    get_file_path
)

def check_status(export_csv=False):
    """
    Check status of all files in the scraping pipeline, including both weekly and monthly data.
    For artist-level data, only checks listeners (not plays).
    """
    html_missing = []
    csv_missing = []
    csv_empty = []
    csv_unreadable = []
    html_empty = []

    # Check both weekly and monthly data
    for period_type, periods in [("weekly", raw_week_endings), ("monthly", raw_month_starts)]:
        # Check song-level data
        for song in songs_to_scrape:
            song_id = song["id"]
            song_name = song["name"]
            valid_periods = periods if period_type == "monthly" else get_valid_weeks_for_song(song)

            for period in valid_periods:
                # For monthly data, only check listeners
                # For weekly data, check both listeners and plays
                measures = ["listeners"] if period_type == "monthly" else ["listeners", "plays"]
                
                for measure in measures:
                    # Get file paths using the same function as the scraping script
                    html_path = get_file_path(
                        period_type=period_type,
                        measure=measure,
                        period_value=period,
                        level="song",
                        song_id=song_id,
                        group_by=group_by
                    )
                    
                    # For monthly data, use a different pattern
                    if period_type == "monthly":
                        csv_path = f"parsed csvs/parsed_monthly_{measure}_by_{group_by}_{song_id}_{period}.csv"
                    else:
                        csv_path = output_csv_file_template.format(
                            period_type=period_type,
                            measure=measure,
                            group_by=group_by,
                            song_id=song_id,
                            week=period
                        )

                    # Check HTML file
                    if not os.path.exists(html_path):
                        html_missing.append((song_name, measure, period, period_type, "Missing HTML", html_path))
                    elif os.path.getsize(html_path) == 0:
                        html_empty.append((song_name, measure, period, period_type, "Empty HTML", html_path))

                    # Check CSV file
                    if not os.path.exists(csv_path):
                        csv_missing.append((song_name, measure, period, period_type, "Missing CSV", csv_path))
                    elif os.path.exists(csv_path):
                        try:
                            df = pd.read_csv(csv_path)
                            if df.empty:
                                csv_empty.append((song_name, measure, period, period_type, "Empty CSV", csv_path))
                            elif len(df) < 2:  # Check if CSV has at least header and one row
                                csv_empty.append((song_name, measure, period, period_type, "CSV has no data rows", csv_path))
                        except Exception as e:
                            csv_unreadable.append((song_name, measure, period, period_type, f"Unreadable CSV ({str(e)})", csv_path))

        # Check artist-level data (only listeners)
        for period in periods:
            # Only check listeners for artist-level data
            measure = "listeners"
            
            html_path = get_file_path(
                period_type=period_type,
                measure=measure,
                period_value=period,
                level="artist",
                song_id="artist",
                group_by=group_by
            )
            
            if period_type == "monthly":
                csv_path = f"parsed csvs/parsed_monthly_{measure}_by_{group_by}_artist_{period}.csv"
            else:
                csv_path = output_csv_file_template.format(
                    period_type=period_type,
                    measure=measure,
                    group_by=group_by,
                    song_id="artist",
                    week=period
                )

            # Check HTML file
            if not os.path.exists(html_path):
                html_missing.append(("Artist Level", measure, period, period_type, "Missing HTML", html_path))
            elif os.path.getsize(html_path) == 0:
                html_empty.append(("Artist Level", measure, period, period_type, "Empty HTML", html_path))

            # Check CSV file
            if not os.path.exists(csv_path):
                csv_missing.append(("Artist Level", measure, period, period_type, "Missing CSV", csv_path))
            elif os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    if df.empty:
                        csv_empty.append(("Artist Level", measure, period, period_type, "Empty CSV", csv_path))
                    elif len(df) < 2:  # Check if CSV has at least header and one row
                        csv_empty.append(("Artist Level", measure, period, period_type, "CSV has no data rows", csv_path))
                except Exception as e:
                    csv_unreadable.append(("Artist Level", measure, period, period_type, f"Unreadable CSV ({str(e)})", csv_path))

    # Combine all issues
    all_issues = html_missing + html_empty + csv_missing + csv_empty + csv_unreadable
    
    if all_issues:
        df = pd.DataFrame(
            all_issues,
            columns=["Song", "Measure", "Period", "Period Type", "Issue", "File Path"]
        )
        
        # Sort by Song, Period Type, Measure, and Period
        df = df.sort_values(["Song", "Period Type", "Measure", "Period"])

        print("\n🔍 Status Report for All Data:\n")
        print(df.to_string(index=False))

        # Print summary by period type
        print("\n📊 Summary:")
        for period_type in ["weekly", "monthly"]:
            period_issues = df[df["Period Type"] == period_type]
            print(f"\n{period_type.capitalize()} Data:")
            print(f"Total issues found: {len(period_issues)}")
            print(f"Missing HTML files: {len(period_issues[period_issues['Issue'] == 'Missing HTML'])}")
            print(f"Empty HTML files: {len(period_issues[period_issues['Issue'] == 'Empty HTML'])}")
            print(f"Missing CSV files: {len(period_issues[period_issues['Issue'] == 'Missing CSV'])}")
            print(f"Empty CSV files: {len(period_issues[period_issues['Issue'] == 'Empty CSV'])}")
            print(f"CSV files with no data rows: {len(period_issues[period_issues['Issue'] == 'CSV has no data rows'])}")
            print(f"Unreadable CSV files: {len(period_issues[period_issues['Issue'].str.contains('Unreadable CSV')])}")

        if export_csv:
            df.to_csv("status-report-all.csv", index=False)
            print("\n📁 Exported report to status-report-all.csv")
    else:
        print("✅ All expected HTML and CSV files are present and non-empty.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="store_true", help="Export status results to CSV")
    args = parser.parse_args()

    check_status(export_csv=args.csv)
