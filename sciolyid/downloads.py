# github.py | functions for syncing a GitHub repo
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

import asyncio
import concurrent.futures
import os
import logging

from git import Repo

import sciolyid.config as config

download_logger = logging.getLogger(config.options["name"] + ".git_downloads")


async def download_github(data, category, item):  # pylint: disable=unused-argument
    download_logger.info("syncing github")
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    loop = asyncio.get_event_loop()
    try:
        os.listdir(config.options["download_dir"])
    except FileNotFoundError:
        download_logger.info("doesn't exist, cloning")
        await loop.run_in_executor(executor, _clone)
        download_logger.info("done cloning")
    else:
        download_logger.info("exists, syncing")
        await loop.run_in_executor(executor, _sync)
        download_logger.info("done syncing")


def _clone():
    Repo.clone_from(
        config.options["github_image_repo_url"],
        config.options["download_dir"],
        multi_options=["--depth=1"],
    )


def _sync():
    downloads = Repo(config.options["download_dir"])
    downloads.remote("origin").fetch()
    downloads.head.reset(working_tree=True)
