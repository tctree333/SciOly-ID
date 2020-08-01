import csv
import imghdr
import os
import random
import shutil
import time
from typing import Callable, Optional, Union

import imagehash
import requests
from PIL import Image

import sciolyid.config as config
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
) -> Optional[str]:
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

    index = verify_repo.index
    index.add("*")
    index.commit(f"add images: id-{user_id}\n\nUsername: {username}")
    push = verify_repo.remote("origin").push(progress=gen_progress(user_id))

    if len(push) == 0:
        return None
    return ""


def gen_progress(user_id: Union[int, str]) -> Callable:
    if isinstance(user_id, int):
        user_id = str(user_id)

    def wrapped_progress(op_code, cur_count, max_count=None, message=""):
        nonlocal user_id
        print("user_id", user_id)
        print("op_code", op_code)
        print("cur_count", cur_count)
        print("max_count", max_count)
        print("message", message, "\n")
        return

    return wrapped_progress


def find_duplicates(image, distance: int = 5) -> list:
    resp = requests.get(config.options["hashes_url"])
    if resp.status_code != 200:
        return ["Failed to get hashes file."]
    if isinstance(image, str):
        image = Image.open(image)
    current_hash = imagehash.phash(image)
    matches = []
    r = csv.reader(resp.text.strip().split("\n"))
    for filename, hash_value in r:
        if current_hash - imagehash.hex_to_hash(hash_value) <= distance:
            matches.append(config.options["base_image_url"] + filename.strip("./"))
    return matches


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
    except:
        return False

    return ext
