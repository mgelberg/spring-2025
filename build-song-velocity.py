import pandas as pd
import glob
import os

def extract_week_from_filename(filename):
    parts = os.path.basename(filename).split("_")
    return parts[-1].replace(".csv","") #last part is the week

def extract_song_id_from_filename(filename):
    parts = os.path.basename(filename).split("_")
    return parts[-2].replace(".csv","") #second to last part is the song id

def extract_group_by_from_filename(filename):
    parts = os.path.basename(filename).split("_")
    return parts[-3].replace(".csv","") #third to last part is the group by value

def load_all_csvs():
    all_files = glob.glob("plays_by_*.csv")
    all_data = []

    for file in all_files:
        week = extract_week_from_filename(file)
        song_id = extract_song_id_from_filename(file)
        group_by = extract_group_by_from_filename(file)
        df = pd.read_csv(file)
        df["Week"] = week
        df["Song ID"] = song_id
        df["Grouping"] = group_by
        all_data.append(df)

    return pd.concat(all_data, ignore_index=True)

def build_velocity(df):
    df["Week"] = pd.to_datetime(df["Week"], format="%Y%m%d")
    df.sort_values(by=["Grouping","Song ID","Week"], inplace=True)

    df["Δ Plays"] = df.groupby(["Grouping","Song ID"])["Current Period"].diff()
    df["% Δ"] = df.groupby(["Grouping","Song ID"])["Current Period"].pct_change() * 100
    return df

def main():
    df = load_all_csvs()
    df = build_velocity(df)
    df.to_csv("song_velocity_table.csv", index=False)
    print("✅ song_velocity_table.csv created with week-over-week changes")

if __name__ == "__main__":
    main()


