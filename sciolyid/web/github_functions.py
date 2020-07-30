import csv
import os
import time
from typing import Union

import discord.utils
import imagehash
from PIL import Image

import sciolyid.config as config
from sciolyid.web.config import logger



def find_duplicates(image, distance: int = 5) -> list:
    if isinstance(image, str):
        image = Image.open(image)
    current_hash = imagehash.phash(image)
    matches = []
    with open(config.options["download_dir"] + "hashes.csv", "r") as f:
        r = csv.reader(f)
        for filename, hash_value in r:
            if current_hash - imagehash.hex_to_hash(hash_value) <= distance:
                matches.append(config.options["base_image_url"] + filename.strip("./"))
    return matches
