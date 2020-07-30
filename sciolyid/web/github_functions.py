import base64
import csv
import os
import time
from typing import Union

import discord.utils
import imagehash
from github import Github, InputGitTreeElement
from PIL import Image

import sciolyid.config as config
from sciolyid.web.config import logger

g = Github(os.environ[config.options["github_token_env"]])

parse = lambda x: "/".join(x.split("/")[-2:]).split(".")[0]

validation_repo = g.get_repo(parse(config.options["validation_repo_id"]))
image_repo = g.get_repo(parse(config.options["github_image_repo_url"]))


def add_images(
    sources: list,
    destinations: Union[str, list],
    user_id: int,
    username: str,
    use_filenames: bool = True,
) -> str:
    logger.info("adding images")
    different_dests = False
    if isinstance(destinations, list):
        if len(destinations) != len(sources):
            logger.info("source/dest invalid")
            raise IndexError("sources and destinations are not the same length")
        different_dests = True

    new_branch_name = f"user-{user_id}t{int(time.time()-1577865600)}"
    master_sha = validation_repo.get_git_ref("heads/master").object.sha
    new_ref = validation_repo.create_git_ref(
        f"refs/heads/{new_branch_name}", master_sha
    )
    logger.info("created branch")
    for i, item in enumerate(sources):
        filename = item.split("/")[-1] if use_filenames else ""
        with open(item, "rb") as f:
            contents = f.read()
        validation_repo.create_file(
            path=f"{destinations[i] if different_dests else destinations}{filename}",
            message=f"add file {filename}",
            content=contents,
            branch=new_branch_name,
        )
        logger.info(f"file {i} created")
    logger.info("all files added!")
    pull = validation_repo.create_pull(
        title=f"Add files: {username}",
        head=new_branch_name,
        base="master",
        body=f"**User:** {discord.utils.escape_markdown(username)}\n**ID:** {user_id}",
        draft=False,
    )
    logger.info("created pull")
    pull.merge(commit_title=f"add files by {username}", merge_method="squash")
    logger.info("merged")
    new_ref.delete()
    logger.info("deleted branch")
    return pull.html_url


def find_duplicates(image, distance: int = 5) -> list:
    if isinstance(image, str):
        image = Image.open(image)
    current_hash = imagehash.phash(image)

    content = image_repo.get_contents("hashes.csv")
    r = csv.reader(content.decoded_content.decode("utf-8").strip().split("\n"))

    matches = []
    for filename, hash_value in r:
        if current_hash - imagehash.hex_to_hash(hash_value) <= distance:
            matches.append(config.options["base_image_url"] + filename.strip("./"))
    return matches
