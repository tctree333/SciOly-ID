import asyncio
import concurrent.futures
import os

import discord
from git import Repo

import sciolyid.config as config
from sciolyid.data import logger

async def download_github():
    logger.info("syncing github")
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    loop = asyncio.get_event_loop()
    try:
        os.listdir(config.options['download_dir'])
    except FileNotFoundError:
        logger.info("doesn't exist, cloning")
        await loop.run_in_executor(executor, _clone)
        logger.info("done cloning")
    else:
        logger.info("exists, pulling")
        await loop.run_in_executor(executor, _pull)
        logger.info("done pulling")

def _clone():
    Repo.clone_from(config.options["github_image_repo_url"], config.options['download_dir'])

def _pull():
    Repo(config.options['download_dir']).remote("origin").pull()