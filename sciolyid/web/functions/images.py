# functions/images.py | functions for working with images
# Copyright (C) 2019-2021  EraserBird, person_v1.32, hmmm

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import csv
import imghdr
import os
from typing import Dict, Optional, Set, Union

import imagehash
import requests
from flask import abort
from PIL import Image

import sciolyid.config as config
from sciolyid.web.config import logger

VALID_MIMETYPES = ("image/jpeg", "image/png")
VALID_IMG_TYPES = ("jpeg", "png")
MAX_FILESIZE = 4000000  # 4 mb


def find_duplicates(image, distance: int = 5, ignore_verify: bool = False) -> list:
    logger.info("find duplicates")
    files: Set[str] = set()
    for url in config.options["hashes_url"]:
        if (
            ignore_verify
            and "/".join(config.options["validation_repo_url"].split("/")[-2:-1]).split(
                ".git"
            )[0]
            in url
        ):
            continue
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.info(
                f"hashes lookup failed: status {resp.status_code}; url {resp.url}"
            )
            return ["Failed to get hashes file."]
        files = files.union(set(map(lambda x: x.strip(), resp.text.split("\n"))))
    files.discard("")

    if isinstance(image, str):
        image = Image.open(image)
    current_hash = imagehash.phash(image)
    matches = []
    r = csv.reader(files)
    for url, image_hash in r:
        if current_hash - imagehash.hex_to_hash(image_hash) <= distance:
            matches.append(url)
    return matches


def generate_id_lookup(ignore_verify: bool = False) -> Optional[Dict[str, str]]:
    logger.info("generate id lookup")
    files: Set[str] = set()
    for url in config.options["ids_url"]:
        if (
            ignore_verify
            and "/".join(config.options["validation_repo_url"].split("/")[-2:-1]).split(
                ".git"
            )[0]
            in url
        ):
            continue
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.info(f"id lookup failed: status {resp.status_code}; url {resp.url}")
            return None
        files = files.union(set(map(lambda x: x.strip(), resp.text.split("\n"))))
    files.discard("")

    lookup = {}
    r = csv.reader(files)
    for filename, image_id in r:
        lookup[filename] = image_id
    logger.info(f"num lookup ids: {len(lookup)}")
    return lookup


def filename_lookup(start_path: str) -> dict:
    id_lookup = generate_id_lookup()
    if not id_lookup:
        abort(404, "filename lookup failed!")
    result = {}
    stack = []
    stack.append(start_path)
    while stack:
        current = stack.pop()
        for child_filename in os.listdir(current):
            child_path = current + "/" + child_filename
            if os.path.isdir(child_path):
                stack.append(child_path)
                continue
            if imghdr.what(child_path) in VALID_IMG_TYPES:
                image_id = id_lookup.get("./" + os.path.relpath(child_path, start_path))
                if image_id:
                    result[image_id] = child_path
    logger.info(f"found {len(result)} files")
    return result


def verify_image(f, mimetype) -> Union[bool, str]:
    if mimetype not in VALID_MIMETYPES:
        return False

    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_FILESIZE:
        return False

    ext = imghdr.what(None, h=f.read())
    if ext not in VALID_IMG_TYPES:
        return False

    try:
        Image.open(f).verify()
    except:  # pylint: disable=bare-except
        return False

    return ext
