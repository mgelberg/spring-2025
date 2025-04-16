from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from config import artist_id, week_ending, measure, group_by, sort_key, sort_order, zoom, output_html_file

# Optional: dynamically populate these based on city slugs from previous pulls
rows = [
    "2643743", "4930956", "6167865", "4887398", "5812944"
]

# Construct URL
print("Constructing URL...")
base_url = f"https://artists.apple.com/ui/measure/artist/{artist_id}/trends"
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

# Launch browser
print("Configuring Chrome browser...")
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

print("Navigating to website...")
driver.get(base_url + params)

print("Waiting for manual login...")
input("Log in manually, then press ENTER to continue...")

print("Waiting for page to load...")
time.sleep(10)

print("Getting page source...")
page_source = driver.page_source

print("Saving to file...")
with open(output_html_file, 'w', encoding='utf-8') as file:
    file.write(page_source)

driver.quit()
print("✅ Done! Saved HTML to:", output_html_file)
