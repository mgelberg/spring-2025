from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from config import week_endings, songs_to_scrape, artist_id, sort_key, sort_order, measure, zoom, song_id, group_by, output_html_file_template

# Optional: add city rows or other filter options as needed
rows = ["2643743", "4930956", "6167865", "4887398", "5812944"]

# Start browser once
print("Starting browser...")
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Visit the first week URL for manual login
initial_week = week_endings[0]
base_url = f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
params = (
    f"?period=w~{initial_week}"
    f"&sortKey={sort_key}"
    f"&sortOrder={sort_order}"
    f"&measure={measure}"
    f"&zoom={zoom}"
    f"&filter=song~{song_id}"
    f"&groupBy={group_by}"
    f"&annotationsVisible=true"
)

print(f"🔗 Navigating to login page for week {initial_week}...")
driver.get(base_url + params)

input("💬 Log in manually, then press ENTER to start scraping...")

# Loop over week + song
for week in week_endings:
    for song in songs_to_scrape:
        song_id = song["id"]
        song_name = song["name"]

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
        time.sleep(10)

        html_file = output_html_file_template.format(week=week, song_id=song_id, group_by=group_by)
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        print(f"✅ Saved HTML to {html_file}")

driver.quit()
print("\n🎉 All pages scraped.")
