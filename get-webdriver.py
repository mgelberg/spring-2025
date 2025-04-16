from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from config import artist_id, week_endings, measure, group_by, sort_key, sort_order, zoom, output_html_file_template

# Optional: dynamically populate these based on city slugs from previous pulls
rows = [
    "2643743", "4930956", "6167865", "4887398", "5812944"
]

# Start browser once
print("🧭 Starting Chrome browser...")
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
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
    f"&groupBy={group_by}"
    f"&annotationsVisible=true"
    + ''.join([f"&rows={r}" for r in rows])
)

print(f"🔗 Navigating to login page for week {initial_week}...")
driver.get(base_url + params)

input("💬 Log in manually, then press ENTER to start scraping...")

# Now loop through all weeks (including the first one again if you like)
for week_ending in week_endings:
    print(f"\n🔄 Scraping week ending {week_ending}...")

    params = (
        f"?period=w~{week_ending}"
        f"&sortKey={sort_key}"
        f"&sortOrder={sort_order}"
        f"&measure={measure}"
        f"&zoom={zoom}"
        f"&groupBy={group_by}"
        f"&annotationsVisible=true"
        + ''.join([f"&rows={r}" for r in rows])
    )
    url = base_url + params
    driver.get(url)

    print("⏳ Waiting for data to load...")
    time.sleep(10)

    page_source = driver.page_source
    output_html_file = output_html_file_template.format(week_ending)
    with open(output_html_file, 'w', encoding='utf-8') as file:
        file.write(page_source)

    print(f"✅ Saved HTML for {week_ending} to {output_html_file}")

# Close browser
driver.quit()
print("\n🎉 All page sources collected!")
