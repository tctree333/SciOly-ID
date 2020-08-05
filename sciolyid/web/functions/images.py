import csv
import imghdr
import os
import shutil
from typing import Dict, Optional, Set, Union

import imagehash
import requests
from PIL import Image

import sciolyid.config as config
import sciolyid.web.tasks.git_tasks as git_tasks
from sciolyid.web.config import logger
from sciolyid.web.git import verify_repo

VALID_MIMETYPES = ("image/jpeg", "image/png")
VALID_IMG_TYPES = ("jpeg", "png")
MAX_FILESIZE = 4000000  # 4 mb


def add_images(
    sources: list,
    destinations: Union[str, list],
    user_id: int,
    username: str,
    use_filenames: bool = True,
):
    different_dests = False
    if isinstance(destinations, list):
        if len(destinations) != len(sources):
            logger.info("source/dest invalid")
            raise IndexError("sources and destinations are not the same length")
        different_dests = True

    verify_repo.remote("origin").pull()
    for i, item in enumerate(sources):
        filename = item.split("/")[-1] if use_filenames else ""
        destination_path = (
            config.options["validation_local_dir"] + destinations[i]
            if different_dests
            else destinations
        )
        os.makedirs(destination_path, exist_ok=True)
        shutil.copyfile(item, destination_path + filename)

    git_tasks.push.delay(f"add images: id-{user_id}\n\nUsername: {username}", user_id)


def find_duplicates(image, distance: int = 5) -> list:
    files: Set[str] = set()
    for url in config.options["hashes_url"]:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return ["Failed to get hashes file."]
        files.union(set(resp.text.strip().split("\n")))

    if isinstance(image, str):
        image = Image.open(image)
    current_hash = imagehash.phash(image)
    matches = []
    r = csv.reader(files)
    for url, image_hash in r:
        if current_hash - imagehash.hex_to_hash(image_hash) <= distance:
            matches.append(url)
    return matches


def generate_id_lookup() -> Optional[Dict[str, str]]:
    files: Set[str] = set()
    for url in config.options["ids_url"]:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        files.union(set(resp.text.strip().split("\n")))

    lookup = {}
    r = csv.reader(files)
    for filename, image_id in r:
        lookup[filename] = image_id
    return lookup


def verify_image(f, mimetype) -> Union[bool, str]:
    if mimetype not in VALID_MIMETYPES:
        return False

    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if not size <= MAX_FILESIZE:
        return False

    ext = imghdr.what(None, h=f.read())
    if ext not in VALID_IMG_TYPES:
        return False

    try:
        Image.open(f).verify()
    except:  # pylint: disable=bare-except
        return False

    return ext
