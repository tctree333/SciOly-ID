# git.py | functions for interacting with git
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

import os

import filelock
import git.repo.fun
from git import Repo

import sciolyid.config as config
from sciolyid.data import logger


def _setup_repo(repo_url: str, repo_dir: str) -> Repo:
    lock = filelock.FileLock(repo_dir.strip("/") + ".lock")
    with lock:
        if os.path.exists(repo_dir) and git.repo.fun.is_git_dir(
            os.path.join(repo_dir, ".git")
        ):
            repo = Repo(repo_dir)
            repo.remote("origin").fetch()
            repo.head.reset(working_tree=True)
        else:
            os.makedirs(repo_dir, exist_ok=True)
            new_repo_url = repo_url.split("/")
            if ":" not in new_repo_url[2] and "@" not in new_repo_url[2]:
                new_repo_url[2] = (
                    os.environ[config.options["git_user_env"]]
                    + ":"
                    + os.environ[config.options["git_token_env"]]
                    + "@"
                    + new_repo_url[2]
                )
            repo = Repo.clone_from("/".join(new_repo_url), repo_dir)

            with repo.config_writer() as cw:
                cw.set_value(
                    "user", "email", os.environ[config.options["git_email_env"]]
                )
                cw.set_value("user", "name", os.environ[config.options["git_user_env"]])

    logger.info("done!")
    return repo


verify_repo: Repo = _setup_repo(
    config.options["validation_repo_url"], config.options["validation_local_dir"]
)
image_repo: Repo = _setup_repo(
    config.options["github_image_repo_url"], config.options["download_dir"]
)
