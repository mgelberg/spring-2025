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
    , measure
    , zoom
    , group_by
    , output_html_file_template
    , get_valid_weeks_for_song
) #removed song_id
import os


# Optional: add city rows or other filter options as needed
rows = ["2643743", "4930956", "6167865", "4887398", "5812944"]

def main():
    # Start browser once
    print("Starting browser...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Track total scrapes and time
    total_scrapes = sum(len(get_valid_weeks_for_song(song)) for song in songs_to_scrape)
    current_scrape = 0
    start_time = time.time()

    print("📊 Scraping Schedule Overview:")
    for song in songs_to_scrape:
        valid_weeks = get_valid_weeks_for_song(song)
        print(f"🎵 {song['name']} — {song['release_date']} — {len(valid_weeks)} weeks pulled")

    # Visit the first week URL for manual login
    initial_song = songs_to_scrape[0]
    initial_week = get_valid_weeks_for_song(initial_song)[0]
    initial_song_id = initial_song["id"]    

    base_url = f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
    params = (
        f"?period=w~{initial_week}"
        f"&sortKey={sort_key}"
        f"&sortOrder={sort_order}"
        f"&measure={measure}"
        f"&zoom={zoom}"
        f"&filter=song~{initial_song_id}"
        f"&groupBy={group_by}"
        f"&annotationsVisible=true"
    )

    print(f"🔗 Navigating to login page for week {initial_week}...")
    driver.get(base_url + params)

    input("💬 Log in manually, then press ENTER to start scraping...")

    # Loop over week + song

    for song in songs_to_scrape:
        song_id = song["id"]
        song_name = song["name"]

        valid_weeks = get_valid_weeks_for_song(song)

        for week in valid_weeks:

            print(f"\n🎧 Scraping: {song_name} | Week: {week}")

            base_url = f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
            params = (
                f"?period=w~{week}"
                f"&sortKey={sort_key}"
                f"&sortOrder={sort_order}"
                f"&measure={measure}"
                f"&zoom={zoom}"
                f"&filter=song~{song_id}"
                f"&groupBy={group_by}"
                f"&annotationsVisible=true"
            )

            driver.get(base_url + params)
            sleep_time = random.uniform(10,19)
            time.sleep(sleep_time)

            html_file = output_html_file_template.format(
                week=week, song_id=song_id, group_by=group_by, measure=measure
            )
            
            os.makedirs(os.path.dirname(html_file), exist_ok=True)

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            current_scrape += 1
            elapsed = time.time() - start_time
            avg_time_per_scrape = elapsed / current_scrape
            remaining = total_scrapes - current_scrape
            eta_seconds = int(avg_time_per_scrape * remaining)
            eta_min = eta_seconds // 60
            eta_sec = eta_seconds % 60

            progress_pct = round((current_scrape / total_scrapes) * 100)

            print(
                f"✅ Saved HTML to {html_file}"
                f"({current_scrape}/{total_scrapes} - {progress_pct}% complete) "
                f"⏳ ETA: {eta_min}m {eta_sec}s"
            )

    driver.quit()
    print("\n🎉 All pages scraped.")

if __name__ == "__main__":
    main()
