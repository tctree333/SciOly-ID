# start_bot.py | main program
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
import sys
from datetime import date, datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks

import sciolyid.config as config
import sciolyid.data
from sciolyid.data import GenericError, database, logger
from sciolyid.data_functions import user_setup, channel_setup
from sciolyid.functions import (
    backup_all,
    evict_images,
    fools,
    get_all_users,
    handle_error,
)
from sciolyid.util import prune_user_cache

# Initialize bot
intent: discord.Intents = discord.Intents.none()
intent.guilds = True
intent.members = config.options["members_intent"]
intent.messages = True
intent.voice_states = True

cache_flags: discord.MemberCacheFlags = discord.MemberCacheFlags.none()
cache_flags.voice = True
cache_flags.joined = config.options["members_intent"]

bot = commands.Bot(
    command_prefix=config.options["prefixes"],
    case_insensitive=True,
    description=config.options["bot_description"],
    help_command=commands.DefaultHelpCommand(verify_checks=False),
    intents=intent,
    member_cache_flags=cache_flags,
)


@bot.event
async def on_ready():
    print("Ready!")
    logger.info("Logged in as:")
    logger.info(bot.user.name)
    logger.info(bot.user.id)
    # Change discord activity
    await bot.change_presence(
        activity=discord.Activity(type=3, name=config.options["id_type"])
    )

    # start tasks
    if config.options["refresh_images"]:
        update_images.start()
    if config.options["evict_images"]:
        refresh_images.start()
    refresh_user_cache.start()
    evict_user_cache.start()
    if config.options["backups_channel"]:
        refresh_backup.start()


# Here we load our extensions(cogs) that are located in the cogs directory, each cog is a collection of commands
initial_extensions = [
    "sciolyid.cogs.media",
    "sciolyid.cogs.check",
    "sciolyid.cogs.skip",
    "sciolyid.cogs.hint",
    "sciolyid.cogs.score",
    "sciolyid.cogs.stats",
    "sciolyid.cogs.sessions",
    "sciolyid.cogs.race",
    "sciolyid.cogs.meta",
    "sciolyid.cogs.other",
]
if config.options["state_roles"]:
    initial_extensions.append("sciolyid.cogs.state")

for extension in config.options["disable_extensions"]:
    try:
        initial_extensions.remove(f"sciolyid.cogs.{extension}")
    except ValueError as e:
        raise config.BotConfigError(
            f"Unable to disable extension 'sciolyid.cogs.{extension}'"
        ) from e

initial_extensions += config.options["custom_extensions"]
initial_extensions = list(set(initial_extensions))

for extension in initial_extensions:
    try:
        bot.load_extension(extension)
    except (
        discord.ClientException,
        ModuleNotFoundError,
        commands.errors.ExtensionFailed,
    ) as e:
        if isinstance(e, commands.errors.ExtensionFailed) and e.args[0].endswith(
            "is already an existing command or alias."
        ):
            raise config.BotConfigError(
                f"short_id_type conflicts with a prexisting command in {extension}"
            )

        raise GenericError(f"Failed to load extension {extension}.", 999) from e


if sys.platform == "win32":
    asyncio.set_event_loop(asyncio.ProactorEventLoop())

######
# Global Command Checks
######


@bot.check
async def prechecks(ctx):
    await ctx.trigger_typing()

    logger.info("global check: checking permissions")
    await commands.bot_has_permissions(
        send_messages=True, embed_links=True, attach_files=True
    ).predicate(ctx)

    logger.info("global check: checking banned")
    if database.zscore("ignore:global", str(ctx.channel.id)) is not None:
        raise GenericError(code=192)
    if database.zscore("banned:global", str(ctx.author.id)) is not None:
        raise GenericError(code=842)

    logger.info("global check: logging command frequency")
    database.zincrby("frequency.command:global", 1, str(ctx.command))

    logger.info("global check: database setup")
    await channel_setup(ctx)
    await user_setup(ctx)

    return True


if config.options["holidays"]:

    @bot.check
    async def is_holiday(ctx):
        """April Fools Prank.

        Can be extended to other holidays as well.
        """
        logger.info("global check: checking holiday")
        now = datetime.now(tz=timezone(-timedelta(hours=4))).date()
        if now == date(now.year, 4, 1):
            return await fools(ctx)
        return True


######
# GLOBAL ERROR CHECKING
######
@bot.event
async def on_command_error(ctx, error):
    """Handles errors for all commands without local error handlers."""
    logger.info("Error: " + str(error))

    # don't handle errors with local handlers
    if hasattr(ctx.command, "on_error"):
        return

    await handle_error(ctx, error)

if config.options["refresh_images"]:

    @tasks.loop(hours=24.0)
    async def update_images():
        """Updates the images."""
        logger.info("updating images")
        await config.options["download_func"](sciolyid.data, None, None)
        logger.info("done updating images!")


if config.options["evict_images"]:

    @tasks.loop(minutes=15.0)
    async def refresh_images():
        """Task to delete a random selection of cached images every hour."""
        logger.info("TASK: Refreshing some cache items")
        event_loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(1) as executor:
            await event_loop.run_in_executor(executor, evict_images)


@tasks.loop(hours=3.0)
async def refresh_user_cache():
    """Task to update User cache to increase performance of commands."""
    logger.info("TASK: Updating User cache")
    await get_all_users(bot)


@tasks.loop(minutes=8.0)
async def evict_user_cache():
    """Task to remove keys from the User cache to ensure freshness."""
    logger.info("TASK: Removing user keys")
    prune_user_cache(10)


@tasks.loop(hours=1.0)
async def refresh_backup():
    """Sends a copy of the database to a discord channel (BACKUPS_CHANNEL)."""
    logger.info("Refreshing backup")
    try:
        os.remove(config.options["backups_dir"] + "dump.dump")
        logger.info("Cleared backup dump")
    except FileNotFoundError:
        logger.info("Already cleared backup dump")
    try:
        os.remove(config.options["backups_dir"] + "keys.txt")
        logger.info("Cleared backup keys")
    except FileNotFoundError:
        logger.info("Already cleared backup keys")

    event_loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(1) as executor:
        await event_loop.run_in_executor(executor, backup_all)

    logger.info("Sending backup files")
    channel = bot.get_channel(config.options["backups_channel"])
    with open(config.options["backups_dir"] + "dump.dump", "rb") as f:
        await channel.send(file=discord.File(f, filename="dump"))
    with open(config.options["backups_dir"] + "keys.txt", "r") as f:
        await channel.send(file=discord.File(f, filename="keys.txt"))
    logger.info("Backup Files Sent!")


# Actually run the bot
token = os.getenv(config.options["bot_token_env"])
bot.run(token)
