# start_bot.py | main program
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

import asyncio
import os
import sys

import discord
import redis
import wikipedia
from discord.ext import commands, tasks
from sentry_sdk import capture_exception

from sciolyid.data import GenericError, database, logger
from sciolyid.functions import channel_setup
from sciolyid.core import download_github
import sciolyid.config as config

# Initialize bot
bot = commands.Bot(
    command_prefix=config.options["prefixes"],
    case_insensitive=True,
    description=config.options["bot_description"],
)

@bot.event
async def on_ready():
    print("Ready!")
    logger.info("Logged in as:")
    logger.info(bot.user.name)
    logger.info(bot.user.id)
    # Change discord activity
    await bot.change_presence(activity=discord.Activity(type=3, name=config.options["id_type"]))

    # start tasks
    update_images.start()

# Here we load our extensions(cogs) that are located in the cogs directory, each cog is a collection of commands
initial_extensions = [
    "sciolyid.cogs.media",
    "sciolyid.cogs.check",
    "sciolyid.cogs.skip",
    "sciolyid.cogs.hint",
    "sciolyid.cogs.score",
    "sciolyid.cogs.sessions",
    "sciolyid.cogs.other",
]
for extension in config.options["disable_extensions"]:
    try:
        initial_extensions.remove(f"sciolyid.cogs.{extension}")
    except ValueError:
        raise config.BotConfigError(f"Unable to disable extension 'sciolyid.cogs.{extension}'")

initial_extensions += config.options["custom_extensions"]
initial_extensions = list(set(initial_extensions))

for extension in initial_extensions:
    try:
        bot.load_extension(extension)
    except (discord.ClientException, ModuleNotFoundError):
        logger.exception(f"Failed to load extension {extension}.")

if sys.platform == "win32":
    asyncio.set_event_loop(asyncio.ProactorEventLoop())

######
# Global Command Checks
######

@bot.check
async def dm_cooldown(ctx):
    """Clears the cooldown in DMs."""
    logger.info("global check: checking dm cooldown clear")
    if ctx.command.is_on_cooldown(ctx) and ctx.guild is None:
        ctx.command.reset_cooldown(ctx)
    return True

@bot.check
async def bot_has_permissions(ctx):
    """Checks if the bot has correct permissions."""
    logger.info("global check: checking permissions")
    # code copied from @commands.bot_has_permissions(send_messages=True, embed_links=True, attach_files=True)
    if ctx.guild is not None:
        perms = {"send_messages": True, "embed_links": True, "attach_files": True}
        guild = ctx.guild
        me = guild.me if guild is not None else ctx.bot.user
        permissions = ctx.channel.permissions_for(me)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]

        if not missing:
            return True

        raise commands.BotMissingPermissions(missing)
    else:
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

    if isinstance(error, commands.CommandOnCooldown):  # send cooldown
        await ctx.send(
            "**Cooldown.** Try again after " + str(round(error.retry_after)) + " s.",
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
            "**The bot does not have enough permissions to fully function.**\n" +
            f"**Permissions Missing:** `{', '.join(map(str, error.missing_perms))}`\n" +
            "*Please try again once the correct permissions are set.*"
        )

    elif isinstance(error, commands.NoPrivateMessage):
        capture_exception(error)
        await ctx.send("**This command is unavaliable in DMs!**")

    elif isinstance(error, GenericError):
        if error.code == 842:
            await ctx.send("**Sorry, you cannot use this command.**")
        elif error.code == 666:
            logger.info("GenericError 666")
        elif error.code == 201:
            logger.info("HTTP Error")
            capture_exception(error)
            await ctx.send("**An unexpected HTTP Error has occurred.**\n *Please try again.*")
        else:
            logger.info("uncaught generic error")
            capture_exception(error)
            await ctx.send(
                "**An uncaught generic error has occurred.**\n" +
                "*Please log this message in #support in the support server below, or try again.*\n" + "**Error:** " +
                str(error)
            )
            await ctx.send(config.options["support_server"])
            raise error

    elif isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, redis.exceptions.ResponseError):
            capture_exception(error.original)
            if database.exists(f"channel:{ctx.channel.id}"):
                await ctx.send(
                    "**An unexpected ResponseError has occurred.**\n" +
                    "*Please log this message in #support in the support server below, or try again.*\n" +
                    "**Error:** " + str(error)
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
            await ctx.send("Wikipedia page unavaliable. Try again later.")

        elif isinstance(error.original, discord.HTTPException):
            if error.original.status == 502:
                await ctx.send("**An error has occured with discord. :(**\n*Please try again.*")
            else:
                capture_exception(error.original)
                await ctx.send(
                    "**An unexpected HTTPException has occurred.**\n" +
                    "*Please log this message in #support in the support server below, or try again*\n" +
                    "**Error:** " + str(error.original)
                )
                await ctx.send(config.options["support_server"])

        #            elif isinstance(error.original, aiohttp.ClientOSError):
        #                if error.original.errno == errno.ECONNRESET:
        #                    await ctx.send("**An error has occured with discord. :(**\n*Please try again.*")
        #                else:
        #                    capture_exception(error.original)
        #                    await ctx.send(
        #                        "**An unexpected ClientOSError has occurred.**\n" +
        #                        "*Please log this message in #support in the support server below, or try again.*\n" +
        #                        "**Error:** " + str(error.original))
        #                    await ctx.send(config.options["support_server"])

        else:
            logger.info("uncaught command error")
            capture_exception(error.original)
            await ctx.send(
                "**An uncaught command error has occurred.**\n" +
                "*Please log this message in #support in the support server below, or try again.*\n" + "**Error:**  " +
                str(error)
            )
            await ctx.send(config.options["support_server"])
            raise error

    else:
        logger.info("uncaught non-command")
        capture_exception(error)
        await ctx.send(
            "**An uncaught non-command error has occurred.**\n" +
            "*Please log this message in #support in the support server below, or try again.*\n" + "**Error:** " +
            str(error)
        )
        await ctx.send(config.options["support_server"])
        raise error

@tasks.loop(hours=24.0)
async def update_images():
    """Updates the images."""
    logger.info("updating github")
    await download_github()
    logger.info("done updating images!")

# Actually run the bot
token = os.getenv(config.options["bot_token_env"])
bot.run(token)
