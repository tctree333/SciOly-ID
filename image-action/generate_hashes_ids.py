import csv
import hashlib
import imghdr
import os

import imagehash
from PIL import Image


def file_type(filename):
    if os.path.isdir(filename):
        return "dir"
    if imghdr.what(filename) not in ("jpeg", "png"):
        return None
    try:
        Image.open(filename).verify()
    except:  # pylint: disable=bare-except
        return None
    return "img"


def get_image_files(start_path):
    os.path.normpath(start_path)
    image_paths = []
    stack = []
    visited = []
    stack.append(start_path)
    visited.append(start_path)
    while stack:
        current = stack.pop()
        for child in os.listdir(current):
            child = current + "/" + child
            if child not in visited:
                visited.append(child)
                thing = file_type(child)
                if thing == "img":
                    image_paths.append(child)
                elif thing == "dir":
                    stack.append(child)
    return image_paths


def calculate_image_hashes(images, start_path, base_url):
    hashes = []
    os.path.normpath(start_path)
    for path in images:
        with Image.open(path) as image:
            image_hash = imagehash.phash(image)
        hashes.append((base_url + os.path.relpath(path, start_path), str(image_hash)))
    return hashes


def calculate_image_ids(images, start_path):
    ids = []
    os.path.normpath(start_path)
    for path in images:
        with open(path, "rb") as f:
            image_id = hashlib.sha1(f.read()).hexdigest()
            ids.append(("./" + os.path.relpath(path, start_path), str(image_id)))
    return ids


def write_hashes(start_path, base_url):
    images = get_image_files(start_path)
    hashes = calculate_image_hashes(images, start_path, base_url)
    with open("hashes.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(hashes)


def write_ids(start_path):
    images = get_image_files(start_path)
    ids = calculate_image_ids(images, start_path)
    with open("ids.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(ids)


# write_hashes(".", "./")
# write_ids(".")
