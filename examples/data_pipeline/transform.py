# [[file:readme.org::+begin_src python :tangle transform.py][No heading:1]]
"""Tiny CSV transform: read from stdin, uppercase the name column, write to stdout."""
import csv
import sys

reader = csv.DictReader(sys.stdin)
writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames, lineterminator="\n")
writer.writeheader()
for row in reader:
    row["name"] = row["name"].upper()
    writer.writerow(row)
# No heading:1 ends here
