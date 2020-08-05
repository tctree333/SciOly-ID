import csv
import hashlib
import imghdr
import os

from PIL import Image


def file_type(filename):
    if os.path.isdir(filename):
        return "dir"
    if imghdr.what(filename) not in ("jpeg", "png"):
        return None
    try:
        Image.open(filename).verify()
    except:
        return None
    return "img"


def get_image_files(start_path):
    start_path = start_path[:-1] if start_path[-1] == "/" else start_path
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


def calculate_image_ids(images, start_path):
    ids = []
    for path in images:
        with open(path, "rb") as f:
            image_id = hashlib.sha1(f.read()).hexdigest()
            path = path.strip(start_path)
            ids.append(("." + path, str(image_id)))
    return ids


def write_ids(start_path):
    images = get_image_files(start_path)
    ids = calculate_image_ids(images, start_path)
    with open("ids.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(ids)


write_ids(".")
