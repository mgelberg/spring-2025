from config import (
    songs_to_scrape,
    # artist_id,
    # sort_key,
    # sort_order,
    # zoom,
    group_by,
    output_html_file_template,
    generate_month_start_dates,
    get_common_parser,
    build_scrape_url,
    start_logged_in_browser,
    scrape_file,
    print_progress,
    get_file_path
)
import os
import time

def parse_args():
    parser = get_common_parser()
    parser.add_argument("--log-urls", action="store_true", default=False, help="Log URLs being requested")
    return parser.parse_args()

def main():
    args = parse_args()
    measures = args.measures
    levels = args.levels
    
    # Start browser
    first_url = build_scrape_url(
        period_value=raw_month_starts[0] if args.period_type == "monthly" else raw_week_endings[0],
        song_id=None if "artist" in levels else songs_to_scrape[0]["id"],
        measure=measures[0],
        period_type=args.period_type
    )
    driver = start_logged_in_browser(first_url)
    
    # Scrape files
    start_time = time.time()
    for i, (level, song_obj, period_value, html_file, measure) in enumerate(pending_scrapes):
        url = build_scrape_url(
            period_value,
            song_obj["id"] if song_obj else None,
            measure=measure,
            period_type=args.period_type,
            log_urls=args.log_urls
        )
        
        current_song_name = song_obj["name"] if song_obj else None

        scrape_file(
            driver,
            url,
            html_file,
            level=level,
            measure=measure,
            period_type=args.period_type,
            period_value=period_value,
            song_name=current_song_name,
            log_urls=args.log_urls
        )
        print_progress(i, len(pending_scrapes), start_time)
    
    driver.quit()
    print("\n🎉 All scraping complete.")

if __name__ == "__main__":
    main()
