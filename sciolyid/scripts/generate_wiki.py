import csv
import sys

import wikipedia
from sciolyid.data import master_id_list

folder = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "data"
with open(f"{folder}/wikipedia.txt", "r") as f:
    urls = {thing: url for thing, url in csv.reader(f)}

fails = []
with open(f"{folder}/wikipedia.txt", "w") as f:
    writer = csv.writer(f)
    for thing in master_id_list:
        print(thing)
        if thing in urls.keys():
            url = urls[thing]
        else:
            try:
                url = wikipedia.page(f"{thing}").url
            except (
                wikipedia.exceptions.DisambiguationError,
                wikipedia.exceptions.PageError,
            ):
                print("FAIL")
                fails.append(thing)
                continue
        writer.writerow((thing, url))

print(fails)
