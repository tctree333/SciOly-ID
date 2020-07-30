import base64
import csv
import os
import time

import imagehash
from PIL import Image

import sciolyid.config as config
from github import Github, InputGitTreeElement

g = Github(os.environ[config.options["github_token_env"]])

get_id = lambda x: "/".join(x.split("/")[-2:]).split(".")[0]

validation_repo = g.get_repo(get_id(config.options["validation_repo_id"]))
image_repo = g.get_repo(get_id(config.options["github_image_repo_url"]))


def add_images(images: list, path: str, user_id: int, username: str):
    new_branch_name = f"user-{user_id}t{int(time.time()-1577865600)}"
    master_sha = validation_repo.get_git_ref("heads/master").object.sha
    new_ref = validation_repo.create_git_ref(
        f"refs/heads/{new_branch_name}", master_sha
    )
    for item in images:
        filename = item.split("/")[-1]
        with open(item, "rb") as f:
            contents = f.read()
        validation_repo.create_file(
            path=f"{path}{filename}",
            message=f"add file {filename}",
            content=contents,
            branch=new_branch_name,
        )
    pull = validation_repo.create_pull(
        title=f"Add files: {username}",
        head=new_branch_name,
        base="master",
        body=f"User:{username}\nID:{user_id}",
        draft=False,
    )
    pull.merge(commit_title=f"add files by {username}", merge_method="squash")
    new_ref.delete()
    return


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
