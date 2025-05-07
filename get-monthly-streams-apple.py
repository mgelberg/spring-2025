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

def parse_args():
    parser = get_common_parser()
    parser.add_argument("--log-urls", action="store_true", help="Log URLs being requested")
    return parser.parse_args()

def main():
    args = parse_args()
    measures = args.measures
    levels = args.levels
    
    # Get valid months for each song
    periods_by_song = {
        song["id"]: [
            month for month in generate_month_start_dates()
            if month >= song["release_date"][:6]  # Only months after release
        ]
        for song in songs_to_scrape
    }
    
    # Print scraping plan
    print("\n📋 Monthly Scraping Plan:")
    for song in songs_to_scrape:
        song_id = song["id"]
        periods = periods_by_song[song_id]
        print(f"�� {song['name']} — {len(periods)} months to scrape")
    
    # Check what needs scraping
    pending_scrapes = []
    for measure in measures:
        for song in songs_to_scrape:
            song_id = song["id"]
            periods = periods_by_song[song_id]
            
            for period_value in periods:
                for level in levels:
                    html_file = get_file_path(
                        period_type="monthly" if period_type == "m" else "weekly",
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
        period_type="monthly"
    )
    driver = start_logged_in_browser(first_url)
    
    # Scrape files
    start_time = time.time()
    for i, (level, song, period_value, html_file, measure) in enumerate(pending_scrapes):
        url = build_scrape_url(
            period_value,
            song["id"] if level == "song" else None,
            measure=measure,
            period_type="monthly"
        )
        
        if args.log_urls:
            print(f"\n🔗 URL for {level} level scrape:")
            print(f"   {url}")
        
        scrape_file(driver, url, html_file)
        
        print_progress(i, len(pending_scrapes), start_time)
    
    driver.quit()
    print("\n🎉 All monthly scraping complete.")

if __name__ == "__main__":
    main()
