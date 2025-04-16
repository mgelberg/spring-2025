import subprocess
from config import week_endings

print("🔁 Step 1: Running get-webdriver.py to fetch all HTML files...")
subprocess.run(["python", "get-webdriver.py"], check=True)

print("\n🧪 Step 2: Parsing each page into CSV...")

for week in week_endings:
    print(f"📄 Parsing data for week ending {week}...")
    subprocess.run(["python", "parse-page-data.py", week], check=True)

print("\n🎉 All exports and parses complete!")