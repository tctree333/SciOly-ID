import wikipedia
from sciolyid.data import id_list

urls = {}
with open(f'data/wikipedia.txt', 'r') as f:
    for line in f:
        thing = line.strip().split(',')[0]
        url = line.strip().split(',')[1]
        urls[thing] = url

fails = []
with open("data/wikipedia.txt", 'w') as f:
    for thing in id_list:
        print(thing)
        if thing in urls.keys():
            url = urls[thing]
        else:
            try:
                url = wikipedia.page(f"{thing}").url
            except Exception:
                print('FAIL')
                fails.append(thing)
                continue
        f.write(f"{thing},{url}\n")

print(fails)
