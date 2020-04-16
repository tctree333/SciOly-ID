# data.py | import data from lists
# Copyright (C) 2019-2020  EraserBird, person_v1.32, hmmm

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

import csv
import logging
import logging.handlers
import os
import sys

import redis
import sentry_sdk
from discord.ext import commands
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.redis import RedisIntegration

import sciolyid.config as config

# define database for one connection
if config.options["local_redis"]:
    database = redis.Redis(host="localhost", port=6379, db=0)
elif config.options["redis_env"] is not None:
    database = redis.from_url(os.getenv(config.options["redis_env"]))
else:
    raise ValueError("redis_env must be set if local_redis is False")

def before_sentry_send(event, hint):
    """Fingerprint certain events before sending to Sentry."""
    if "exc_info" in hint:
        error = hint["exc_info"][1]
        if isinstance(error, commands.CommandNotFound):
            event["fingerprint"] = ["command-not-found"]
        elif isinstance(error, commands.CommandOnCooldown):
            event["fingerprint"] = ["command-cooldown"]
    return event

# add sentry logging
if config.options["sentry"]:
    if config.options["sentry_dsn_env"] is None:
        raise ValueError("sentry_dsn_env must be set if sentry is True")
    sentry_sdk.init(
        release=f"Heroku Release {os.getenv('HEROKU_RELEASE_VERSION')}:{os.getenv('HEROKU_SLUG_DESCRIPTION')}",
        dsn=os.getenv(config.options["sentry_dsn_env"]),
        integrations=[RedisIntegration(), AioHttpIntegration()],
        before_send=before_sentry_send,
    )

# Database Format Definitions

# prevJ - makes sure it sends a diff image
# prevI - makes sure it sends a diff item (img)

# server format = {
# channel:channel_id : { "item", "answered",
#                     "prevJ", "prevI" }
# }

# session format:
# session.data:user_id : {"start": 0, "stop": 0,
#                         "correct": 0, "incorrect": 0, "total": 0,
#                         "bw": bw, "group": group}
# session.incorrect:user_id : [item name, # incorrect]

# race format:
# race.data:ctx.channel.id : {
#                    "start": 0
#                    "stop": 0,
#                    "limit": 10,
#                    "bw": bw,
#                    "group": group
# }
# race.scores:ctx.channel.id : [ctx.author.id, #correct]

# leaderboard format = {
#    users:global : [user id, # of correct]
#    users.server:server_id : [user id, # of correct]
# }

# streaks format = {
#    streak:global : [user id, current streak]
#    streak.max:global : [user id, max streak]
# }

# incorrect item format = {
#    incorrect:global : [item name, # incorrect]
#    incorrect.server:server_id : [item name, # incorrect]
#    incorrect.user:user_id: : [item name, # incorrect]
# }

# channel score format = {
#   score:global : [channel id, # of correct]
# }

# ban format:
#   banned:global : [user id, 0]

# setup logging
logger = logging.getLogger(config.options["name"])
if config.options["logs"]:
    logger.setLevel(logging.DEBUG)
    os.makedirs(f"{config.options['log_dir']}", exist_ok=True)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        f"{config.options['log_dir']}/log.txt", backupCount=4, when="midnight"
    )
    file_handler.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    file_handler.setFormatter(
        logging.Formatter("{asctime} - {filename:10} -  {levelname:8} - {message}", style="{")
    )
    stream_handler.setFormatter(logging.Formatter("{filename:10} -  {levelname:8} - {message}", style="{"))

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # log uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

class GenericError(commands.CommandError):
    """A custom error class.

    Error codes: (can add more if needed)\n
        0 - no code
        111 - Index Error
        201 - HTTP Error
        999 - Invalid
        990 - Invalid Input
        100 - Blank
        842 - Banned User
        666 - No output error
    """
    def __init__(self, message=None, code=0):
        self.code = code
        super().__init__(message=message)

# Error codes: (can add more if needed)
# 0 - no code
# 111 - Index Error
# 201 - HTTP Error
# 999 - Invalid
# 990 - Invalid Input
# 100 - Blank
# 842 - Banned User
# 666 - No output error

def _wiki_urls():
    logger.info("Working on wiki urls")
    urls = {}
    with open(f'{config.options["wikipedia_file"]}', 'r') as f:
        reader = csv.reader(f)
        for item, url in reader:
            urls[item.lower()] = url
    logger.info("Done with wiki urls")
    return urls

def get_wiki_url(item: str):
    return wikipedia_urls[item.lower()]

def _generate_aliases():
    logger.info("Working on aliases")
    aliases = {}
    with open(f'{config.options["alias_file"]}', 'r') as f:
        reader = csv.reader(f)
        for raw_aliases in reader:
            raw_aliases = list(map(str.lower, raw_aliases))
            item = raw_aliases[0]
            aliases[item] = raw_aliases
    logger.info("Done with aliases")
    return aliases

def get_aliases(item: str):
    logger.info(f"getting aliases for {item}")
    item = item.lower()
    try:
        logger.info("aliases found")
        return aliases[item]
    except KeyError:
        logger.info("no aliases")
        return [item]

def get_category(item: str):
    logger.info(f"getting category for item {item}")
    item = item.lower()
    for group in groups:
        if item in groups[group]:
            logger.info(f"category found: {group}")
            return group.lower()
    logger.info(f"no category found for item {item}")
    return None

def _groups():
    """Converts txt files of data into lists."""
    filenames = [name.split(".")[0] for name in os.listdir(f"{config.options['list_dir']}/")]
    # Converts txt file of data into lists
    lists = {}
    for filename in filenames:
        logger.info(f"Working on {filename}")
        with open(f'{config.options["list_dir"]}/{filename}.txt', "r") as f:
            lists[filename] = [line.strip().lower() for line in f]
        logger.info(f"Done with {filename}")
    logger.info("Done with lists!")
    return lists

def _all_lists():
    """Compiles lists into master lists."""
    master = []
    for group in groups:
        for item in groups[group]:
            master.append(item)
    master = list(set(master))
    return master

def _config():
    for group in groups:
        if group not in config.options["category_aliases"].keys():
            config.options["category_aliases"][group] = [group]

    _aliases = [item for group in groups.keys() for item in config.options["category_aliases"][group]]
    if len(_aliases) != len(set(_aliases)):
        raise config.BotConfigError("Aliases in category_aliases not unique")

groups = _groups()
id_list = _all_lists()
wikipedia_urls = _wiki_urls()
aliases = _generate_aliases()
_config()
logger.info(f"List Lengths: {len(id_list)}")

logger.info("Done importing data!")
