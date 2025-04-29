import subprocess
from config import songs_to_scrape, group_by, get_valid_weeks_for_song

def main():
    print("🔁 Step 1: Fetch all HTML files")
    subprocess.run(["python", "get-webdriver.py"], check=True)

    print("\n📊 Step 2: Parse song + week combos")
    for song in songs_to_scrape:
        song_id = song["id"]
        valid_weeks = get_valid_weeks_for_song(song)

        for week in valid_weeks:
            subprocess.run(["python", "parse-page-data.py", week, song["id"], group_by], check=True)

    print("✅ All done!")

if __name__ == "__main__":
    main()