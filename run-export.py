import subprocess
import argparse
from config import songs_to_scrape, group_by, get_valid_weeks_for_song, measures

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force overwrite all outputs")
    return parser.parse_args()


def main():
    args = parse_args()
    force_flag = "--force" if args.force else ""

    print("🔁 Step 1: Fetch all HTML files")
    html_cmd = ["python", "get-webdriver.py"]
    if args.force:
        html_cmd.append("--force")
    subprocess.run(html_cmd, check=True)

    print("\n📊 Step 2: Parse song + week combos")
    for measure in measures:

        for song in songs_to_scrape:
            song_id = song["id"]
            valid_weeks = get_valid_weeks_for_song(song)

            for week in valid_weeks:
                cmd = ["python", "parse-page-data.py"
                       , week
                       , song["id"]
                       , group_by
                       , measure]
                if args.force:
                    cmd.append("--force")
                subprocess.run(cmd, check=True)

    print("✅ All done!")

if __name__ == "__main__":
    main()