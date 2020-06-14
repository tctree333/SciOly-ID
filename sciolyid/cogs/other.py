# other.py | misc. commands
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

import itertools
import random
import typing
from difflib import get_close_matches

import discord
import wikipedia
from discord.ext import commands

import sciolyid.config as config
from sciolyid.core import send_image
from sciolyid.data import (aliases, database, get_aliases, groups, id_list,
                           logger, master_id_list, meme_list)
from sciolyid.functions import CustomCooldown, build_id_list


class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Info - Gives image
    @commands.command(
        help=f"- Gives images of specific {config.options['id_type']}", aliases=["i"]
    )
    @commands.check(CustomCooldown(10.0, bucket=commands.BucketType.user))
    async def info(self, ctx, *, arg):
        logger.info("command: info")

        matches = get_close_matches(
            arg.lower(),
            master_id_list + list(itertools.chain.from_iterable(aliases.values())),
            n=1,
        )
        if matches:
            item = matches[0]

            if item in itertools.chain.from_iterable(aliases.values()):
                logger.info("matched alias! getting item name.")
                item = next(key for key, value in aliases.items() if item in value)

            delete = await ctx.send("Please wait a moment.")
            await send_image(ctx, str(item), message=f"Here's a *{item.lower()}* image!")
            await delete.delete()

        else:
            await ctx.send(
                f"{config.options['id_type'][:-1].title()} not found. Are you sure it's on the list?"
            )

    # List command
    @commands.command(help="- DMs the user with the appropriate list.", name="list")
    @commands.check(CustomCooldown(8.0, bucket=commands.BucketType.user))
    async def list_of_items(self, ctx, group=""):
        logger.info("command: list")

        build = build_id_list(group)
        group_list = build[0]
        detected_groups = "total items" if build[1] == "None" else build[1]

        item_lists = []
        temp = ""
        for item in group_list:
            temp += f"{item}\n"
            if len(temp) > 1950:
                item_lists.append(temp)
                temp = ""
        item_lists.append(temp)

        if ctx.author.dm_channel is None:
            await ctx.author.create_dm()

        await ctx.author.dm_channel.send(
            f"**{detected_groups.capitalize()} in the National {config.options['id_type'][:-1].title()} list:**"
        )
        for group in item_lists:
            await ctx.author.dm_channel.send(f"```\n{group}```")

        await ctx.send(
            f"The National {config.options['id_type'][:-1].title()} list has **{len(group_list)}** {detected_groups}.\n"
            + f"*A full list of {detected_groups} has been sent to you via DMs.*"
        )

    # Group command - lists groups
    if config.options["id_groups"]:

        @commands.command(
            help="- Prints a list of all available groups.",
            aliases=[
                config.options["category_name"].lower(),
                config.options["category_name"].lower() + "s",
                "group",
                "category",
                "categories",
            ],
        )
        @commands.check(CustomCooldown(8.0, bucket=commands.BucketType.user))
        async def groups(self, ctx):
            logger.info("command: list")

            await ctx.send(f"**Valid Groups**: `{', '.join(map(str, list(groups.keys())))}`")

    # Wiki command - argument is the wiki page
    @commands.command(help="- Fetch the wikipedia page for any given argument")
    @commands.check(CustomCooldown(8.0, bucket=commands.BucketType.user))
    async def wiki(self, ctx, *, arg):
        logger.info("command: wiki")

        try:
            page = wikipedia.page(arg)
            await ctx.send(page.url)
        except wikipedia.exceptions.DisambiguationError:
            await ctx.send("Sorry, that page was not found. Try being more specific.")
        except wikipedia.exceptions.PageError:
            await ctx.send("Sorry, that page was not found.")

    if config.options["meme_file"]:
        # meme command - sends a random item video/gif
        @commands.command(
            help=f"- Sends a funny {config.options['id_type'][:-1]} video/image!"
        )
        @commands.cooldown(1, 300.0, type=commands.BucketType.user)
        async def meme(self, ctx):
            logger.info("command: meme")

            if meme_list:
                await ctx.send(random.choice(meme_list))
            else:
                await ctx.send("No memes avaliable :(")

    if config.options["sendas"]:
        # Send command - for testing purposes only
        @commands.command(help="- send command", hidden=True, aliases=["sendas"])
        @commands.is_owner()
        async def send_as_bot(self, ctx, *, args_str):
            logger.info("command: send")

            logger.info(f"args: {args_str}")
            args = args_str.split(" ")

            channel_id = int(args[0])
            try:
                message = args[1:]
            except IndexError:
                await ctx.send("No message provided!")
            channel = self.bot.get_channel(channel_id)
            await channel.send(" ".join(message))
            await ctx.send("Ok, sent!")

    # Test command - for testing purposes only
    @commands.command(help="- test command", hidden=True)
    async def test(self, ctx, *, item):
        logger.info("command: test")
        await ctx.send(await get_aliases(item))

    # Test command - for testing purposes only
    @commands.command(help="- test command", hidden=True)
    async def error(self, ctx):
        logger.info("command: error")
        await ctx.send(1 / 0)


def setup(bot):
    bot.add_cog(Other(bot))
