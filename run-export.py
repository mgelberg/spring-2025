import subprocess

print("🔁 Starting export process...")

# Step 1: Get the HTML
print("▶ Running get-webdriver.py...")
subprocess.run(["python", "get-webdriver.py"], check=True)

# Step 2: Parse and export CSV
print("▶ Running parse-page-data.py...")
subprocess.run(["python", "parse-page-data.py"], check=True)

print("✅ All done!")