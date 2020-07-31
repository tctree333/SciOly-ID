import csv
import os
import time
import random
import shutil
from typing import Union, Optional

import time
import imagehash
import requests
from git import Repo
from PIL import Image

import sciolyid.config as config
from sciolyid.web.config import logger

while os.path.exists(config.options["bot_files_dir"] + "git.lock"):
    logger.info("waiting...")
    time.sleep(random.random())
with open(config.options["bot_files_dir"] + "git.lock", "w") as f:
    f.write("locked")
logger.info("locked")

verify_repo: Repo
if os.path.exists(config.options["validation_local_dir"]):
    verify_repo = Repo(config.options["validation_local_dir"])
    verify_repo.remote("origin").fetch()
    verify_repo.head.reset(working_tree=True)
else:
    os.makedirs(config.options["validation_local_dir"])
    repo_url = config.options["validation_repo_url"].split("/")
    repo_url[2] = (
        os.environ[config.options["git_user_env"]]
        + ":"
        + os.environ[config.options["git_token_env"]]
        + "@"
        + repo_url[2]
    )
    verify_repo = Repo.clone_from(
        "/".join(repo_url), config.options["validation_local_dir"]
    )
os.remove(config.options["bot_files_dir"] + "git.lock")
logger.info("done!")

with verify_repo.config_writer() as cw:
    cw.set("user.email", os.environ[config.options["git_email_env"]])
    cw.set("user.name", os.environ[config.options["git_user_env"]])

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
    index.add(config.options["validation_local_dir"] + "*")
    index.commit(f"add images: id-{user_id}\n\nUsername: {username}", )
    push = verify_repo.remote("origin").push()

    if len(push) == 0:
        return None
    for p in push:
        print(p, p.remote_ref_string)
    return push[0].remote_ref_string


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
