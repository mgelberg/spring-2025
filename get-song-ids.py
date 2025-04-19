from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Start at Apple Music for Artists
driver.get("https://artists.apple.com/")

input("🧑‍💻 Log in and navigate to the Songs tab, then press ENTER...")

# Give it a second to fully load
time.sleep(5)

# Try grabbing ALL elements that look like song rows
# (You may need to adjust this based on actual class names or structure)
possible_rows = driver.find_elements(By.XPATH, "//div[contains(text(), 'Plays')]/ancestor::div[7]")

print(f"🔎 Found {len(possible_rows)} potential song rows.")

# Dump info for inspection
for i, row in enumerate(possible_rows[:10]):
    print(f"\n--- Song Row #{i+1} ---")
    print(row.text)
    print("--- HTML ---")
    print(row.get_attribute("outerHTML"))

driver.quit()