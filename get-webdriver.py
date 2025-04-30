from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
from config import (
    songs_to_scrape
    , artist_id
    , sort_key
    , sort_order
    , measures
    , zoom
    , group_by
    , output_html_file_template
    , get_valid_weeks_for_song
) #removed song_id
import os
import argparse


# Optional: add city rows or other filter options as needed
rows = ["2643743", "4930956", "6167865", "4887398", "5812944"]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force re-download HTML files")
    return parser.parse_args()

def main():
    args = parse_args()
    force = args.force
    

 
    print("📊 Scraping Schedule Overview:")
    
    for song in songs_to_scrape:
        valid_weeks = get_valid_weeks_for_song(song)
        print(f"🎵 {song['name']} — {song['release_date']} — {len(valid_weeks)} weeks pulled")

    # Check what actually needs scraping
    pending_scrapes = []
    for measure in measures:
        for song in songs_to_scrape:
            song_id = song["id"]
            valid_weeks = get_valid_weeks_for_song(song)

            for week in valid_weeks:
                html_file = output_html_file_template.format(
                    week=week, song_id=song_id, group_by=group_by, measure=measure
                )
                if not os.path.exists(html_file) or force:
                    pending_scrapes.append((measure, song, week, html_file))
    
    if not pending_scrapes:  # NEW
        print("✅ No new HTML files to scrape. Everything is already up to date.")
        return  # NEW

    # Start browser once
    print("Starting browser...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Manual login flow
    first_measure, first_song, first_week, _ = pending_scrapes[0]  # NEW
    song_id = first_song["id"]
    login_url = (
        f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
        f"?period=w~{first_week}"
        f"&sortKey={sort_key}"
        f"&sortOrder={sort_order}"
        f"&measure={first_measure}"
        f"&zoom={zoom}"
        f"&filter=song~{song_id}"
        f"&groupBy={group_by}"
        f"&annotationsVisible=true"
    )

    print(f"🔗 Navigating to login page for week {first_week}...")
    driver.get(login_url)

    input("💬 Log in manually, then press ENTER to start scraping...")

    start_time = time.time()
    for i, (measure, song, week, html_file) in enumerate(pending_scrapes):
        song_id = song["id"]
        song_name = song["name"]

        print(f"\n🎧 Scraping: {song_name} | Week: {week} | Measure: {measure}")  # CHANGED

        url = (
            f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
            f"?period=w~{week}"
            f"&sortKey={sort_key}"
            f"&sortOrder={sort_order}"
            f"&measure={measure}"
            f"&zoom={zoom}"
            f"&filter=song~{song_id}"
            f"&groupBy={group_by}"
            f"&annotationsVisible=true"
        )

        driver.get(url)
        time.sleep(random.uniform(10, 19))

        os.makedirs(os.path.dirname(html_file), exist_ok=True)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        elapsed = time.time() - start_time
        progress = i + 1
        eta = int((elapsed / progress) * (len(pending_scrapes) - progress))
        print(
            f"✅ Saved HTML to {html_file} "
            f"({progress}/{len(pending_scrapes)} — {round(100 * progress / len(pending_scrapes))}% complete) "
            f"⏳ ETA: {eta // 60}m {eta % 60}s"
        )

    driver.quit()
    print("\n🎉 All scraping complete.")


if __name__ == "__main__":
    main()
