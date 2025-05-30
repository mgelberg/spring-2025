from config import (
    songs_to_scrape,
    group_by,
    get_common_parser,
    build_scrape_url,
    start_logged_in_browser,
    scrape_file,
    print_progress,
    get_file_path
)
import time
import os

def parse_args():
    parser = get_common_parser()
    parser.add_argument("--log-urls", action="store_true", help="Log URLs being requested")
    return parser.parse_args()

def main():
    args = parse_args()
    measures = args.measures
    levels = args.levels
    
    # Check what needs scraping
    pending_scrapes = []
    for measure in measures:
        for level in levels:
            if level == "artist":
                # For artist level, use raw_week_endings
                for period_value in raw_week_endings:
                    html_file = get_file_path(
                        period_type="weekly",
                        measure=measure,
                        period_value=period_value,
                        level=level,
                        song_id="artist",
                        group_by=group_by
                    )
                    if not os.path.exists(html_file) or args.force:
                        pending_scrapes.append((level, None, period_value, html_file, measure))
            else:
                # For song level, iterate through songs
                for song in songs_to_scrape:
                    song_id = song["id"]
                    for period_value in get_valid_weeks_for_song(song):
                        html_file = get_file_path(
                            period_type="weekly",
                            measure=measure,
                            period_value=period_value,
                            level=level,
                            song_id=song_id,
                            group_by=group_by
                        )
                        if not os.path.exists(html_file) or args.force:
                            pending_scrapes.append((level, song, period_value, html_file, measure))
    
    if not pending_scrapes:
        print("✅ No new HTML files to scrape. Everything is already up to date.")
        return
    
    # Start browser
    first_scrape = pending_scrapes[0]
    first_url = build_scrape_url(
        first_scrape[2],  # period_value
        first_scrape[1]["id"] if first_scrape[0] == "song" else None,
        measure=first_scrape[4],
        period_type="weekly"
    )
    driver = start_logged_in_browser(first_url)
    
    # Scrape files
    start_time = time.time()
    for i, (level, song_obj, period_value, html_file, measure) in enumerate(pending_scrapes):
        url = build_scrape_url(
            period_value,
            song_obj["id"] if song_obj else None,
            measure=measure,
            period_type="weekly",
            log_urls=args.log_urls
        )
        
        current_song_name = song_obj["name"] if song_obj else None

        scrape_file(
            driver,
            url,
            html_file,
            level=level,
            measure=measure,
            period_type="weekly",
            period_value=period_value,
            song_name=current_song_name,
            log_urls=args.log_urls
        )
        print_progress(i, len(pending_scrapes), start_time)
    
    driver.quit()
    print("\n🎉 All weekly scraping complete.")

if __name__ == "__main__":
    main()
