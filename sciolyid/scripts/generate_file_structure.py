import os

def _groups():
    """Converts txt files of data into lists."""
    filenames = [name[:name.rfind(".")] for name in os.listdir("/bot/data/lists")]
    # Converts txt file of data into lists
    lists = {}
    for filename in filenames:
        print(f"Working on {filename}")
        with open(f'/bot/data/lists/{filename}.txt', 'r') as f:
            lists[filename] = [line.strip().lower() for line in f]
        print(f"Done with {filename}")
    print("Done with lists!")
    return lists

groups = _groups()

for key in groups:
    for item in groups[key]:
        os.makedirs(f"{key}/{item}")
        with open(f"{key}/{item}/image.placeholder", "x") as f:
            f.write("")
