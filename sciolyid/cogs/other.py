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
import typing
from difflib import get_close_matches

import discord
import wikipedia
from discord.ext import commands

import sciolyid.config as config
from sciolyid.data import database, get_aliases, id_list, logger, aliases, groups
from sciolyid.functions import channel_setup, owner_check, user_setup, build_id_list
from sciolyid.core import send_image

class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Info - Gives image
    @commands.command(help=f"- Gives an image of {config.options['id_type']}", aliases=["i"])
    @commands.cooldown(1, 10.0, type=commands.BucketType.user)
    async def info(self, ctx, *, arg):
        logger.info("command: info")

        await channel_setup(ctx)
        await user_setup(ctx)

        matches = get_close_matches(
            arg.lower(),
            id_list + list(itertools.chain.from_iterable(aliases.values())),
            n=1,
        )
        if matches:
            item = matches[0]

            delete = await ctx.send("Please wait a moment.")
            await send_image(ctx, str(item), message=f"Here's a *{item.lower()}* image!")
            await delete.delete()

        else:
            await ctx.send(f"{config.options['id_type'].title()} not found. Are you sure it's on the list?")

    # List command
    @commands.command(help="- DMs the user with the appropriate list.", name="list")
    @commands.cooldown(1, 8.0, type=commands.BucketType.user)
    async def list_of_items(self, ctx, group=""):
        logger.info("command: list")

        await channel_setup(ctx)
        await user_setup(ctx)

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
            f"**{detected_groups.capitalize()} in the National {config.options['id_type']} list:**"
        )
        for group in item_lists:
            await ctx.author.dm_channel.send(f"```\n{group}```")

        await ctx.send(
            f"The national {config.options['id_type']} list has **{len(group_list)}** {detected_groups}.\n" +
            f"*A full list of {detected_groups} has been sent to you via DMs.*"
        )

    # Group command - lists groups
    @commands.command(
        help="- DMs the user with the appropriate list.",
        aliases=["taxons", "group", "categories"],
    )
    @commands.cooldown(1, 8.0, type=commands.BucketType.user)
    async def groups(self, ctx):
        logger.info("command: list")

        await channel_setup(ctx)
        await user_setup(ctx)

        await ctx.send(f"**Valid Groups**: `{', '.join(map(str, list(groups.keys())))}`")

    # Wiki command - argument is the wiki page
    @commands.command(help="- Fetch the wikipedia page for any given argument")
    @commands.cooldown(1, 8.0, type=commands.BucketType.user)
    async def wiki(self, ctx, *, arg):
        logger.info("command: wiki")

        await channel_setup(ctx)
        await user_setup(ctx)

        try:
            page = wikipedia.page(arg)
            await ctx.send(page.url)
        except wikipedia.exceptions.DisambiguationError:
            await ctx.send("Sorry, that page was not found. Try being more specific.")
        except wikipedia.exceptions.PageError:
            await ctx.send("Sorry, that page was not found.")

    # bot info command - gives info on bot
    @commands.command(
        help="- Gives info on bot, support server invite, stats",
        aliases=["bot_info", "support", "stats"],
    )
    @commands.cooldown(1, 5.0, type=commands.BucketType.channel)
    async def botinfo(self, ctx):
        logger.info("command: botinfo")

        await channel_setup(ctx)
        await user_setup(ctx)

        embed = discord.Embed(type="rich", colour=discord.Color.blurple())
        embed.set_author(name=config.options["bot_signature"])
        embed.add_field(
            name="Bot Info",
            value=f"This bot was created by {config.options['authors']}" +
            f" for helping people practice {config.options['id_type']} identification for Science Olympiad.\n" +
            f"The bot's source can be found here: {config.options['source_link']}",
            inline=False,
        )
        embed.add_field(
            name="Support",
            value="If you are experiencing any issues, have feature requests, " +
            "or want to get updates on bot status, join our support server below.",
            inline=False,
        )
        embed.add_field(
            name="Stats",
            value=f"This bot can see {len(self.bot.users)} users and is in {len(self.bot.guilds)} servers. " +
            f"There are {int(database.zcard('users:global'))} active users in {int(database.zcard('score:global'))} channels. "
            + f"The WebSocket latency is {round(self.bot.latency*1000)} ms.",
            inline=False,
        )
        await ctx.send(embed=embed)
        await ctx.send(config.options["support_server"])

    # invite command - sends invite link
    @commands.command(help="- Get the invite link for this bot")
    @commands.cooldown(1, 5.0, type=commands.BucketType.channel)
    async def invite(self, ctx):
        logger.info("command: invite")

        await channel_setup(ctx)
        await user_setup(ctx)

        embed = discord.Embed(type="rich", colour=discord.Color.blurple())
        embed.set_author(name=config.options["bot_signature"])
        embed.add_field(
            name="Invite",
            value=f"To invite this bot to your own server, use the following invite links.\n {config.options['invite']}",
            inline=False,
        )
        await ctx.send(embed=embed)
        await ctx.send(config.options["support_server"])

    # ban command - prevents certain users from using the bot
    @commands.command(help="- ban command", hidden=True)
    @commands.check(owner_check)
    async def ban(self, ctx, *, user: discord.Member = None):
        logger.info("command: ban")
        if user is None or isinstance(user, str):
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        database.zadd("banned:global", {str(user.id): 0})
        await ctx.send(f"Ok, {user.name} cannot use the bot anymore!")

    # unban command - prevents certain users from using the bot
    @commands.command(help="- unban command", hidden=True)
    @commands.check(owner_check)
    async def unban(self, ctx, *, user: typing.Optional[typing.Union[discord.Member, str]] = None):
        logger.info("command: unban")
        if user is None or isinstance(user, str):
            logger.info("no args")
            await ctx.send("Invalid User!")
            return
        logger.info(f"user-id: {user.id}")
        database.zrem("banned:global", str(user.id))
        await ctx.send(f"Ok, {user.name} can use the bot!")

    # Send command - for testing purposes only
    @commands.command(help="- send command", hidden=True, aliases=["sendas"])
    @commands.check(owner_check)
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
        await channel.send(message)
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
