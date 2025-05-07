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
    #, measures
    , zoom
    , group_by
    , output_html_file_template
    #, get_valid_weeks_for_song
    , generate_month_start_dates
) #removed song_id
import os
import argparse


# Optional: add city rows or other filter options as needed
rows = ["2643743", "4930956", "6167865", "4887398", "5812944"]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force re-download HTML files")
    parser.add_argument("--monthly", action="store_true", help="Scrape only monthly listener data")
    return parser.parse_args()

def main():
    args = parse_args()
    force = args.force
    is_monthly = args.monthly
    

 
    
    #print("📊 Scraping Schedule Overview:")
    
    # for song in songs_to_scrape:
    #     valid_weeks = get_valid_weeks_for_song(song)
    #     print(f"🎵 {song['name']} — {song['release_date']} — {len(valid_weeks)} weeks pulled")

    if is_monthly:
        measures = ["listeners_monthly"]
        url_measure = "listeners" if measures[0] == "listeners_monthly" else measures[0]
        periods_by_song = {
            song["id"]: generate_month_start_dates() for song in songs_to_scrape
        }
    else:
        from config import measures, get_valid_weeks_for_song
        periods_by_song = {
            song["id"]: get_valid_weeks_for_song(song) for song in songs_to_scrape
        }
    # NEW — Show scraping plan summary based on actual periods being used
    print("\n📋 Scraping Plan Overview:")
    for song in songs_to_scrape:
        song_id = song["id"]
        for measure in measures:
            periods = periods_by_song.get(song_id, [])
            print(f"🎵 {song['name']} — {measure} — {len(periods)} periods scheduled")

    # Check what actually needs scraping
    pending_scrapes = []
    for measure in measures:
        for song in songs_to_scrape:
            song_id = song["id"]
            periods = periods_by_song[song_id]

            for period_value in periods:
                period_type = "monthly" if is_monthly else "weekly"
                html_file = output_html_file_template.format(
                    week=period_value, song_id=song_id, group_by=group_by, measure=measure, period_type=period_type
                )
                print(f"🔍 Checking file: {html_file}")
                if not os.path.exists(html_file) or force:
                    pending_scrapes.append((measure, song, period_value, html_file))
    
    if not pending_scrapes:  # NEW
        print("✅ No new HTML files to scrape. Everything is already up to date.")
        return  # NEW


    ## commenting out what we'd be passing to chrome
    # # Start browser once
    # print("Starting browser...")
    # options = webdriver.ChromeOptions()
    # options.add_argument("--start-maximized")
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # # Manual login flow
    # first_measure, first_song, first_period, _ = pending_scrapes[0] 
    # first_url_measure = "listeners" if first_measure == "listeners_monthly" else first_measure
    # song_id = first_song["id"]
    # login_url = (
    #     f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
    #     f"?period={'m' if is_monthly else 'w'}~{first_period}"
    #     f"&sortKey={sort_key}"
    #     f"&sortOrder={sort_order}"
    #     f"&measure={first_url_measure}"
    #     f"&zoom={zoom}"
    #     f"&filter=song~{song_id}"
    #     f"&groupBy={group_by}"
    #     f"&annotationsVisible=true"
    # )

    # print(f"🔗 Navigating to login page for {'month' if is_monthly else 'week'} of {first_period}...")
    # driver.get(login_url)

    # input("💬 Log in manually, then press ENTER to start scraping...")

    # start_time = time.time()
    for i, (measure, song, period_value, html_file) in enumerate(pending_scrapes):
        period_prefix = "m" if is_monthly else "w"
        period_value_for_url = period_value[:6] if is_monthly else period_value
        song_id = song["id"]
        song_name = song["name"]

        # print(f"\n🎧 Scraping: {song_name} | Period: {period_value} | Measure: {measure}")  # CHANGED

        url = (
            f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
            f"?period={period_prefix}~{period_value_for_url}"
            f"&sortKey={sort_key}"
            f"&sortOrder={sort_order}"
            f"&measure={url_measure}"
            f"&zoom={zoom}"
            f"&filter=song~{song_id}"
            f"&groupBy={group_by}"
            f"&annotationsVisible=true"
        )
        print(f"🌐 Requesting URL: {url}")
        # driver.get(url)
        # time.sleep(random.uniform(10, 19))

        # os.makedirs(os.path.dirname(html_file), exist_ok=True)
        # with open(html_file, "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)

        # elapsed = time.time() - start_time
        # progress = i + 1
        # eta = int((elapsed / progress) * (len(pending_scrapes) - progress))
        # print(
        #     f"✅ Saved HTML to {html_file} "
        #     f"({progress}/{len(pending_scrapes)} — {round(100 * progress / len(pending_scrapes))}% complete) "
        #     f"⏳ ETA: {eta // 60}m {eta % 60}s"
        # )

    # driver.quit()
    # print("\n🎉 All scraping complete.")

        print(f"\n{i+1}. {song_name} | Period: {period_value} | Measure: {measure}")
        print(f"   URL: {url}")
        print(f"   Output file: {html_file}")

    print("\n🎉 URL generation complete.")


if __name__ == "__main__":
    main()
