import base64
import csv
import os
import time

import imagehash
from PIL import Image

import sciolyid.config as config
from github import Github, InputGitTreeElement

g = Github(os.environ[config.options["github_token_env"]])
repo = g.get_repo(config.options["validation_repo_id"])


def add_images(images: list, path: str, user_id: int, username: str):
    new_branch_name = f"user-{user_id}t{int(time.time()-1577865600)}"
    master_sha = repo.get_git_ref("heads/master").object.sha
    new_ref = repo.create_git_ref(f"refs/heads/{new_branch_name}", master_sha)
    for item in images:
        filename = item.split("/")[-1]
        with open(item, "rb") as f:
            contents = f.read()
        repo.create_file(
            path=f"{path}{filename}",
            message=f"add file {filename}",
            content=contents,
            branch=new_branch_name,
        )
    pull = repo.create_pull(
        title="New Pull Request",
        head=new_branch_name,
        base="master",
        body="add files",
        draft=False,
    )
    pull.merge(commit_title="add files", merge_method="squash")
    new_ref.delete()


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
