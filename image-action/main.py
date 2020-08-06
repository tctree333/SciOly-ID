#!/usr/local/bin/python
import os

from github import Github, Repository

from generate_hashes_ids import (calculate_image_hashes, calculate_image_ids,
                                 get_image_files)

REPO_ID = os.environ["INPUT_CURRENT_REPO"]
SUBFOLDER = os.getenv("INPUT_SUBFOLDER") in (True, "yes", "true", "True")

DEFAULT_URL = f"https://raw.githubusercontent.com/{REPO_ID}/master/"

g = Github(os.environ["INPUT_GITHUB_TOKEN"])
repo: Repository.Repository = g.get_repo(REPO_ID)


def update_files(start_path, base_url):
    images = get_image_files(start_path)

    hashes = "\n".join(
        map(",".join, calculate_image_hashes(images, start_path, base_url))
    )
    ids = "\n".join(map(",".join, calculate_image_ids(images, start_path)))

    hashes_csv = repo.get_contents(f"{os.path.normpath(start_path)}/hashes.csv")
    ids_csv = repo.get_contents(f"{os.path.normpath(start_path)}/ids.csv")

    repo.update_file(hashes_csv.path, "Update hashes.csv", hashes, hashes_csv.sha)
    repo.update_file(ids_csv.path, "Update ids.csv", ids, ids_csv.sha)


url = DEFAULT_URL
if SUBFOLDER:
    for directory in os.listdir("."):
        if (
            not os.path.isdir(directory)
            or len(set(os.listdir(directory)).intersection({"hashes.csv", "ids.csv"}))
            != 2
        ):
            continue
        url += f"{directory}/"
        update_files(f"./{directory}", url)

else:
    update_files(".", url)
