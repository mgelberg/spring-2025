import subprocess
from config import week_endings, songs_to_scrape, group_by

def main():
    print("🔁 Step 1: Fetch all HTML files")
    subprocess.run(["python", "get-webdriver.py"], check=True)

    print("\n📊 Step 2: Parse song + week combos")
    for week in week_endings:
        for song in songs_to_scrape:
            subprocess.run(["python", "parse-page-data.py", week, song["id"], group_by], check=True)

    print("✅ All done!")

if __name__ == "__main__":
    main()