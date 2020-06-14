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
import datetime
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
        release=f"Deployed Discord Bot at {datetime.datetime.today()}",
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
# session.data:user_id : {
#                    "start": 0,
#                    "stop": 0,
#                    "correct": 0,
#                    "incorrect": 0,
#                    "total": 0,
#                    "bw": bw, - Toggles if "bw", doesn't if empty (""), default ""
#                    "group": group,
#                    "wiki": wiki, - Enables if "wiki", disables if empty (""), default "wiki"
#                    "strict": strict - Enables strict spe
# session.incorrect:user_id : [item name, # incorrect]

# race format:
# race.data:ctx.channel.id : {
#                    "start": 0
#                    "stop": 0,
#                    "limit": 10,
#                    "bw": bw,
#                    "group": group,
#                    "strict": strict - Enables strict spelling if "strict", disables if empty, default ""
# }
# race.scores:ctx.channel.id : [ctx.author.id, #correct]

# leaderboard format = {
#    users:global : [user id, # of correct]
#    users.server:guild_id : [user id, # of correct]
# }

# streaks format = {
#    streak:global : [user id, current streak]
#    streak.max:global : [user id, max streak]
# }

# incorrect item format = {
#    incorrect:global : [item name, # incorrect]
#    incorrect.server:guild_id : [item name, # incorrect]
#    incorrect.user:user_id: : [item name, # incorrect]
# }

# item frequency format = {
#   frequency.item:global : [item name, # displayed]
# }

# command frequency format = {
#   frequency.command:global : [command, # used]
# }

# channel score format = {
#   score:global : [channel id, # of correct]
#   channels:global : ["guild id:channel id", 0]
# }

# daily update format = {
#     daily.score:YYYY-MM-DD : [user id, # correct today]
#     daily.incorrect:YYYY-MM-DD : [item name, # incorrect today]
# }

# ban format:
#   banned:global : [user id, 0]

# ignore format:
#   ignore:global : [channel id, guild id]

# leave confirm format:
#   leave:guild_id : 0

# setup logging
logger = logging.getLogger(config.options["name"])
if config.options["logs"]:
    logger.setLevel(logging.DEBUG)
    os.makedirs(config.options["log_dir"], exist_ok=True)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        f"{config.options['log_dir']}log.txt", backupCount=4, when="midnight"
    )
    file_handler.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    file_handler.setFormatter(
        logging.Formatter("{asctime} - {filename:10} -  {levelname:8} - {message}", style="{")
    )
    stream_handler.setFormatter(
        logging.Formatter("{filename:10} -  {levelname:8} - {message}", style="{")
    )

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
    with open(f'{config.options["wikipedia_file"]}', "r") as f:
        reader = csv.reader(f)
        for item, url in reader:
            urls[item.lower()] = url
    logger.info("Done with wiki urls")
    return urls


def get_wiki_url(ctx, item: str):
    logger.info("fetching wiki url")
    if database.hget(f"session.data:{ctx.author.id}", "wiki") == b"":
        logger.info("disabling preview")
        return f"<{wikipedia_urls[item.lower()]}>"
    return wikipedia_urls[item.lower()]


def _generate_aliases():
    logger.info("Working on aliases")
    aliases = {}
    with open(f'{config.options["alias_file"]}', "r") as f:
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
    filenames = [name.split(".")[0] for name in os.listdir(config.options["list_dir"])]
    restricted_filenames = []
    if config.options["restricted_list_dir"]:
        restricted_filenames = [
            name.split(".")[0] for name in os.listdir(config.options["restricted_list_dir"])
        ]

    # Converts txt file of data into lists
    lists = {}
    for filename in filenames:
        logger.info(f"Working on {filename}")
        with open(f'{config.options["list_dir"]}{filename}.txt', "r") as f:
            lists[filename] = [line.strip().lower() for line in f]
        logger.info(f"Done with {filename}")

    for restricted_filename in restricted_filenames:
        logger.info(f"Working on {restricted_filename}")
        with open(
            f'{config.options["restricted_list_dir"]}{restricted_filename}.txt', "r"
        ) as f:
            lists[restricted_filename] = [line.strip().lower() for line in f]
        logger.info(f"Done with {restricted_filename}")

    logger.info("Done with lists!")
    return lists


def _memes():
    """Converts a txt file of memes/video urls into a list."""
    logger.info("Working on memes")
    if config.options["meme_file"]:
        with open(f'{config.options["meme_file"]}', "r") as f:
            memes = [line.strip() for line in f]
        logger.info("Done with memes")
        return memes
    return []


def _all_lists():
    """Compiles lists into master lists."""
    id_list = []
    master_id_list = []
    restricted = []
    if config.options["restricted_list_dir"]:
        restricted = [
            name.split(".")[0] for name in os.listdir(config.options["restricted_list_dir"])
        ]
    for group in groups:
        if group in restricted:
            for item in groups[group]:
                master_id_list.append(item)
        else:
            for item in groups[group]:
                id_list.append(item)
                master_id_list.append(item)
    id_list = list(set(id_list))
    master_id_list = list(set(master_id_list))
    return id_list, master_id_list


def _config():
    for group in groups:
        if group not in config.options["category_aliases"].keys():
            config.options["category_aliases"][group] = [group]

    _aliases = [
        item for group in groups.keys() for item in config.options["category_aliases"][group]
    ]
    if len(_aliases) != len(set(_aliases)):
        raise config.BotConfigError("Aliases in category_aliases not unique")

    if config.options["download_func"] is None:
        from sciolyid.github import download_github

        config.options["download_func"] = download_github


groups = _groups()
meme_list = _memes()
id_list, master_id_list = _all_lists()
wikipedia_urls = _wiki_urls()
aliases = _generate_aliases()
_config()
logger.info(f"List Lengths: {len(id_list)}")
logger.info(f"Master List Lengths: {len(master_id_list)}")

logger.info("Done importing data!")
