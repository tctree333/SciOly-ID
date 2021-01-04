import csv

import imagehash


def get_hashlist():
    hashes = list()
    filenames = list()
    with open("hashes.csv", "r") as f:
        reader = csv.reader(f)
        for filename, img_hash in reader:
            hashes.append(img_hash)
            filenames.append(filename)
    return (hashes, filenames)


def find_duplicates(hashes, filenames):
    duplicates = []
    for i, img_hash in enumerate(hashes):
        matches = [filenames[i]]
        img_hash = imagehash.hex_to_hash(img_hash)
        for j, other_hash in enumerate(hashes):
            other_hash = imagehash.hex_to_hash(other_hash)
            if filenames[i] != filenames[j] and img_hash - other_hash <= 5:
                matches.append(filenames[j])
        if len(matches) > 1:
            duplicates.append(matches)
    return duplicates


print(find_duplicates(*get_hashlist()))
