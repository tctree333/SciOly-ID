import os
import random
import time

from git import Repo

import sciolyid.config as config
from sciolyid.data import logger


def _lock():
    sleep_cycle = 0
    time.sleep(random.random())
    while os.path.exists(config.options["bot_files_dir"] + "git.lock"):
        logger.info("waiting...")
        sleep_cycle += 1
        time.sleep(random.random())
        if sleep_cycle > 120:
            os.remove(config.options["bot_files_dir"] + "git.lock")
    with open(config.options["bot_files_dir"] + "git.lock", "w") as f:
        f.write("locked")
    logger.info("locked")


def _setup_repo(repo_url: str, repo_dir: str) -> Repo:
    _lock()
    repo: Repo
    if os.path.exists(repo_dir):
        repo = Repo(repo_dir)
        repo.remote("origin").fetch()
        repo.head.reset(working_tree=True)
    else:
        os.makedirs(repo_dir)
        new_repo_url = repo_url.split("/")
        new_repo_url[2] = (
            os.environ[config.options["git_user_env"]]
            + ":"
            + os.environ[config.options["git_token_env"]]
            + "@"
            + new_repo_url[2]
        )
        repo = Repo.clone_from(
            "/".join(new_repo_url), repo_dir
        )
    os.remove(config.options["bot_files_dir"] + "git.lock")
    logger.info("done!")

    with repo.config_writer() as cw:
        cw.set_value("user", "email", os.environ[config.options["git_email_env"]])
        cw.set_value("user", "name", os.environ[config.options["git_user_env"]])
    return repo


verify_repo: Repo = _setup_repo(config.options["validation_repo_url"], config.options["validation_local_dir"])
image_repo: Repo = _setup_repo(config.options["github_image_repo_url"], config.options["download_dir"])
