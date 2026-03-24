import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
in_path = os.path.join(script_dir, "output.csv")
out_path = os.path.join(script_dir, "output_simple.csv")

with open(in_path, newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["freq", "nocore", "withcore"])
    for row in rows[1:]:  # skip header
        writer.writerow([row[2], row[7], row[12]])

print(f"Written to {out_path}")
