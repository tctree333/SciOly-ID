import wikipedia
import csv
from sciolyid.data import id_list

with open(f'data/wikipedia.txt', 'r') as f:
    urls = {thing: url for thing, url in csv.reader(f)}

fails = []
with open("data/wikipedia.txt", 'w') as f:
    writer = csv.writer(f)
    for thing in id_list:
        print(thing)
        if thing in urls.keys():
            url = urls[thing]
        else:
            try:
                url = wikipedia.page(f"{thing}").url
            except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
                print('FAIL')
                fails.append(thing)
                continue
        writer.writerow((thing, url))

print(fails)
