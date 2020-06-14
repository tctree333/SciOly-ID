import os
import sys

data_folder = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "/data"
images_folder = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else "/images"


def _groups():
    """Converts txt files of data into lists."""
    filenames = [name[: name.rfind(".")] for name in os.listdir(f"{data_folder}/lists")]
    # Converts txt file of data into lists
    lists = {}
    for filename in filenames:
        print(f"Working on {filename}")
        with open(f"{data_folder}/lists/{filename}.txt", "r") as f:
            lists[filename] = [line.strip().lower() for line in f]
        print(f"Done with {filename}")
    print("Done with lists!")
    return lists


groups = _groups()

for key in groups:
    for item in groups[key]:
        os.makedirs(f"{images_folder}/{key}/{item}")
        with open(f"{images_folder}/{key}/{item}/image.placeholder", "x") as f:
            f.write("")
