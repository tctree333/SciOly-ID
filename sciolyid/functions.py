# functions.py | function definitions
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
import errno
import itertools
import os
import pickle
import shutil
from typing import Iterable, Union

import aiohttp
import discord
import redis
import wikipedia
from discord.ext import commands
from sentry_sdk import capture_exception

import sciolyid.config as config
from sciolyid.data import (
    GenericError,
    all_categories,
    database,
    dealias_group,
    get_category,
    groups,
    id_list,
    logger,
    states,
)
from sciolyid.data_functions import channel_setup
from sciolyid.util import fetch_get_user


def check_state_role(ctx) -> list:
    """Returns a list of state roles a user has.

    `ctx` - Discord context object
    """
    logger.info("checking roles")
    if not config.options["state_roles"]:
        return []
    user_states = []
    if ctx.guild is not None:
        logger.info("server context")
        user_role_names = [role.name.lower() for role in ctx.author.roles]
        for state in states:
            # gets similarities
            if set(user_role_names).intersection(set(states[state]["aliases"])):
                user_states.append(state)
    else:
        logger.info("dm context")
    logger.info(f"user roles: {user_states}")
    return user_states


async def send_leaderboard(
    ctx, title, page, database_key=None, data=None, items_per_page=10
):
    logger.info("building/sending leaderboard")

    if database_key is None and data is None:
        raise GenericError("database_key and data are both NoneType", 990)
    if database_key is not None and data is not None:
        raise GenericError("database_key and data are both set", 990)

    if page < 1:
        page = 1

    entry_count = (
        int(database.zcard(database_key)) if database_key is not None else data.count()
    )
    page = (page * 10) - 10

    if entry_count == 0:
        logger.info(f"no items in {database_key}")
        await ctx.send("There are no items in the database.")
        return

    if page > entry_count:
        page = entry_count - (entry_count % 10)

    leaderboard_list = (
        map(
            lambda x: (x[0].decode("utf-8"), x[1]),
            database.zrevrangebyscore(
                database_key, "+inf", "-inf", page, items_per_page, True
            ),
        )
        if database_key is not None
        else data.iloc[page : page + items_per_page - 1].items()
    )
    embed = discord.Embed(type="rich", colour=discord.Color.blurple())
    embed.set_author(name=config.options["bot_signature"])
    leaderboard = ""

    for i, stats in enumerate(leaderboard_list):
        leaderboard += f"{i+1+page}. **{stats[0]}** - {int(stats[1])}\n"
    embed.add_field(name=title, value=leaderboard, inline=False)

    await ctx.send(embed=embed)


def build_id_list(
    categories: Union[str, Iterable] = "", state: Union[str, Iterable] = ""
):
    """Generates an ID list based on given arguments

    - `categories`: category string/Iterable
    - `state`: state string/Iterable
    """
    logger.info("building id list")
    if isinstance(categories, str):
        categories = categories.split(" ")
    if isinstance(state, str):
        state = state.split(" ")

    id_choices = []
    group_args = set(
        map(dealias_group, all_categories.intersection(set(map(str.lower, categories))))
    )
    state_args = set(states.keys()).intersection(set(map(str.upper, state)))
    logger.info(f"group_args: {group_args}, state_args: {state_args}")

    if not config.options["id_groups"]:
        logger.info("no groups allowed")
        group_args = set()

    if group_args:
        items_in_group = set(
            itertools.chain.from_iterable(groups.get(o, []) for o in group_args)
        )
        if state_args:
            items_in_state = set(
                itertools.chain(*(states[state]["list"] for state in state_args))
            )
            id_choices = list(items_in_group.intersection(items_in_state))
        else:
            id_choices = list(items_in_group.intersection(set(id_list)))
    elif state_args:
        id_choices = list(
            set(itertools.chain(*(states[state]["list"] for state in state_args)))
        )
    else:
        id_choices = id_list

    logger.info(f"id_choices length: {len(id_choices)}")
    return id_choices


def backup_all():
    """Backs up the database to a file.

    This function serializes all data in the REDIS database
    into a file in the `backups` directory.

    This function is run with a task every 6 hours and sends the files
    to a specified discord channel.
    """
    logger.info("Starting Backup")
    logger.info("Creating Dump")
    keys = (key.decode("utf-8") for key in database.keys())
    dump = ((database.dump(key), key) for key in keys)
    logger.info("Finished Dump")
    logger.info("Writing To File")
    try:
        os.mkdir(config.options["backups_dir"])
        logger.info("Created backups directory")
    except FileExistsError:
        logger.info("Backups directory exists")
    with open(config.options["backups_dir"] + "dump.dump", "wb") as f:
        with open(config.options["backups_dir"] + "keys.txt", "w") as k:
            for item, key in dump:
                pickle.dump(item, f)
                k.write(f"{key}\n")
    logger.info("Backup Finished")


async def fools(ctx):
    logger.info(f"holiday check: invoked command: {str(ctx.command)}")
    if str(ctx.command) in ("leaderboard", "missed", "score", "streak", "userscore"):
        embed = discord.Embed(
            type="rich",
            colour=discord.Color.blurple(),
            title=f"{str(ctx.command).title()}",
        )
        embed.set_author(name=config.options["bot_signature"])
        embed.add_field(
            name=f"{str(ctx.command).title()}",
            value="User scores and data have been cleared. We apologize for the inconvenience.",
            inline=False,
        )
        await ctx.send(embed=embed)
        raise GenericError(code=666)
    return True


async def get_all_users(bot):
    logger.info("Starting user cache")
    user_ids = map(int, database.zrangebyscore("users:global", "-inf", "+inf"))
    for user_id in user_ids:
        await fetch_get_user(user_id, bot=bot, member=False)
    logger.info("User cache finished")


def evict_images():
    """Deletes images for items that have exceeded a certain frequency.

    This prevents images from being stale. If the item frequency has
    been incremented more than 10 times, this function will delete the
    top 3 items.
    """
    logger.info("Updating cached images")

    for item in map(
        lambda x: x.decode(),
        database.zrevrangebyscore(
            "frequency.item.refresh:global", "+inf", min=10, start=0, num=3
        ),
    ):
        database.zadd("frequency.item.refresh:global", {item: 0})
        category = get_category(item)
        path = f"{config.options['download_dir']}{category}/{item.lower()}/"
        if os.path.exists(path):
            shutil.rmtree(path)


class CustomCooldown:
    """Halve cooldown times in DM channels."""

    # Code adapted from discord.py example
    def __init__(
        self,
        per: float,
        disable: bool = False,
        bucket: commands.BucketType = commands.BucketType.channel,
    ):
        """Initialize a custom cooldown.

        `per` (float) - Cooldown default duration, halves in DM channels
        `bucket` (commands.BucketType) - cooldown scope, defaults to channel
        """
        rate = 1
        dm_per = per / 2
        race_per = 0.5
        self.disable = disable
        self.default_mapping = commands.CooldownMapping.from_cooldown(rate, per, bucket)
        self.dm_mapping = commands.CooldownMapping.from_cooldown(rate, dm_per, bucket)
        self.race_mapping = commands.CooldownMapping.from_cooldown(
            rate, race_per, bucket
        )

    def __call__(self, ctx: commands.Context):
        if not self.disable and ctx.guild is None:
            # halve cooldown in DMs
            bucket = self.dm_mapping.get_bucket(ctx.message)

        elif ctx.command.name.startswith("check") and ctx.channel.name.startswith(
            "racing"
        ):
            # tiny check cooldown in racing channels
            bucket = self.race_mapping.get_bucket(ctx.message)

        else:
            bucket = self.default_mapping.get_bucket(ctx.message)

        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True


async def handle_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):  # send cooldown
        await ctx.send(
            "**Cooldown.** Try again after " + str(round(error.retry_after, 2)) + " s.",
            delete_after=5.0,
        )

    elif isinstance(error, commands.CommandNotFound):
        capture_exception(error)
        await ctx.send("Sorry, the command was not found.")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("This command requires an argument!")

    elif isinstance(error, commands.BadArgument):
        await ctx.send("The argument passed was invalid. Please try again.")

    elif isinstance(error, commands.ArgumentParsingError):
        await ctx.send("An invalid character was detected. Please try again.")

    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(
            "**The bot does not have enough permissions to fully function.**\n"
            + f"**Permissions Missing:** `{', '.join(map(str, error.missing_perms))}`\n"
            + "*Please try again once the correct permissions are set.*"
        )

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "You do not have the required permissions to use this command.\n"
            + f"**Required Perms:** `{'`, `'.join(error.missing_perms)}`"
        )

    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("**This command is unavailable in DMs!**")

    elif isinstance(error, commands.PrivateMessageOnly):
        await ctx.send("**This command is only available in DMs!**")

    elif isinstance(error, commands.NotOwner):
        logger.info("not owner")
        await ctx.send("Sorry, the command was not found.")

    elif isinstance(error, GenericError):
        if error.code == 192:
            # channel is ignored
            return
        if error.code == 842:
            await ctx.send("**Sorry, you cannot use this command.**")
        elif error.code == 666:
            logger.info("GenericError 666")
        elif error.code == 201:
            logger.info("HTTP Error")
            capture_exception(error)
            await ctx.send(
                "**An unexpected HTTP Error has occurred.**\n *Please try again.*"
            )
        else:
            logger.info("uncaught generic error")
            capture_exception(error)
            await ctx.send(
                "**An uncaught generic error has occurred.**\n"
                + "*Please log this message in #support in the support server below, or try again.*\n"
                + f"**Error code:** `{error.code}`"
            )
            await ctx.send(config.options["support_server"])
            raise error

    elif isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, redis.exceptions.ResponseError):
            capture_exception(error.original)
            if database.exists(f"channel:{ctx.channel.id}"):
                await ctx.send(
                    "**An unexpected ResponseError has occurred.**\n"
                    + "*Please log this message in #support in the support server below, or try again.*\n"
                )
                await ctx.send(config.options["support_server"])
            else:
                await channel_setup(ctx)
                await ctx.send("Please run that command again.")

        elif isinstance(error.original, wikipedia.exceptions.DisambiguationError):
            await ctx.send("Wikipedia page not found. (Disambiguation Error)")

        elif isinstance(error.original, wikipedia.exceptions.PageError):
            await ctx.send("Wikipedia page not found. (Page Error)")

        elif isinstance(error.original, wikipedia.exceptions.WikipediaException):
            capture_exception(error.original)
            await ctx.send("Wikipedia page unavailable. Try again later.")

        elif isinstance(error.original, discord.Forbidden):
            if error.original.code == 50007:
                await ctx.send(
                    "I was unable to DM you. Check if I was blocked and try again."
                )
            elif error.original.code == 50013:
                await ctx.send(
                    "There was an error with permissions. Check the bot has proper permissions and try again."
                )
            else:
                capture_exception(error)
                await ctx.send(
                    "**An unexpected Forbidden error has occurred.**\n"
                    + "*Please log this message in #support in the support server below, or try again.*\n"
                    + f"**Error code:** `{error.original.code}`"
                )
                await ctx.send(config.options["support_server"])

        elif isinstance(error.original, discord.HTTPException):
            capture_exception(error.original)
            if error.original.status == 502:
                await ctx.send(
                    "**An error has occured with discord. :(**\n*Please try again.*"
                )
            else:
                await ctx.send(
                    "**An unexpected HTTPException has occurred.**\n"
                    + "*Please log this message in #support in the support server below, or try again*\n"
                    + f"**Reponse Code:** `{error.original.status}`"
                )
                await ctx.send(config.options["support_server"])

        elif isinstance(error.original, aiohttp.ClientOSError):
            capture_exception(error.original)
            if error.original.errno == errno.ECONNRESET:
                await ctx.send(
                    "**An error has occured with discord. :(**\n*Please try again.*"
                )
            else:
                await ctx.send(
                    "**An unexpected ClientOSError has occurred.**\n"
                    + "*Please log this message in #support in the support server below, or try again.*\n"
                    + "**Error:** "
                    + str(error.original)
                )
                await ctx.send(config.options["support_server"])

        elif isinstance(error.original, aiohttp.ServerDisconnectedError):
            capture_exception(error.original)
            await ctx.send("**The server disconnected.**\n*Please try again.*")

        elif isinstance(error.original, asyncio.TimeoutError):
            capture_exception(error.original)
            await ctx.send("**The request timed out.**\n*Please try again in a bit.*")

        elif isinstance(error.original, OSError):
            capture_exception(error.original)
            if error.original.errno == errno.ENOSPC:
                await ctx.send(
                    "**No space is left on the server!**\n"
                    + "*Please report this message in #support in the support server below!*\n"
                )
                await ctx.send(config.options["support_server"])
            else:
                await ctx.send(
                    "**An unexpected OSError has occurred.**\n"
                    + "*Please log this message in #support in the support server below, or try again.*\n"
                    + f"**Error code:** `{error.original.errno}`"
                )
                await ctx.send(config.options["support_server"])

        else:
            logger.info("uncaught command error")
            capture_exception(error.original)
            await ctx.send(
                "**An uncaught command error has occurred.**\n"
                + "*Please log this message in #support in the support server below, or try again.*\n"
            )
            await ctx.send(config.options["support_server"])
            raise error

    else:
        logger.info("uncaught non-command")
        capture_exception(error)
        await ctx.send(
            "**An uncaught non-command error has occurred.**\n"
            + "*Please log this message in #support in the support server below, or try again.*\n"
        )
        await ctx.send(config.options["support_server"])
        raise error
