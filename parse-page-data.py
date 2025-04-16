import re
import pandas as pd
from bs4 import BeautifulSoup
from config import week_ending, group_by, measure, output_html_file

# Load the saved page source
with open(output_html_file, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Extract all visible text
visible_text = soup.get_text(separator="\n", strip=True)
lines = visible_text.split("\n")

# Find city table start
start_index = None
for i, line in enumerate(lines):
    if line.strip() == "City" and i + 3 < len(lines):
        if (
            lines[i + 1].strip() == "Previous Period" and
            lines[i + 2].strip() == "This Period" and
            lines[i + 3].strip() == "Change"
        ):
            start_index = i + 4
            break

# Parse city data
parsed_rows = []
if start_index is not None:
    i = start_index
    while i + 3 < len(lines):
        city = lines[i].strip()
        prev = lines[i + 1].strip()
        curr = lines[i + 2].strip()
        change = lines[i + 3].strip()
        if not city or not prev.isdigit() or not curr.isdigit():
            break
        parsed_rows.append({
            "City": city,
            "Previous Period": int(prev),
            "Current Period": int(curr),
            "% Change": change,
            "Date": week_ending,
            "Group By": group_by
        })
        i += 4

# Save to CSV
df = pd.DataFrame(parsed_rows)
filename = f"{measure}_by_{group_by}_{week_ending}.csv"
df.to_csv(filename, index=False)
print(f"✅ Saved CSV: {filename}")
