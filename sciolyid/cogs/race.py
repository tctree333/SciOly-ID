# race.py | commands for racing/competition
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

import datetime
import time

import discord
from discord.ext import commands
from discord.utils import escape_markdown as esc

import sciolyid.config as config
from sciolyid.data import (
    all_categories,
    database,
    dealias_group,
    logger,
    states,
)
from sciolyid.functions import CustomCooldown
from sciolyid.util import fetch_get_user


class Race(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _get_options(ctx):
        bw, state, group, limit, strict = database.hmget(
            f"race.data:{ctx.channel.id}", ["bw", "state", "group", "limit", "strict"]
        )
        options = (
            f"**Black & White:** {bw==b'bw'}\n"
            + (
                f"**{config.options['category_name']}:** {group.decode('utf-8') if group else 'None'}\n"
                if config.options["id_groups"]
                else ""
            )
            + f"**Alternate List:** {state.decode('utf-8') if state else 'None'}\n"
            + f"**Amount to Win:** {limit.decode('utf-8')}\n"
            + f"**Strict Spelling:** {strict == b'strict'}"
        )

        return options

    async def _send_stats(self, ctx, preamble):
        placings = 5
        database_key = f"race.scores:{ctx.channel.id}"
        if database.zcard(database_key) == 0:
            logger.info(f"no users in {database_key}")
            await ctx.send("There are no users in the database.")
            return

        if placings > database.zcard(database_key):
            placings = database.zcard(database_key)

        leaderboard_list = database.zrevrangebyscore(
            database_key, "+inf", "-inf", 0, placings, True
        )
        embed = discord.Embed(
            type="rich", colour=discord.Color.blurple(), title=preamble
        )
        embed.set_author(name=config.options["bot_signature"])
        leaderboard = ""

        for i, stats in enumerate(leaderboard_list):
            if ctx.guild is not None:
                user = await fetch_get_user(int(stats[0]), ctx=ctx, member=True)
            else:
                user = None

            if user is None:
                user = await fetch_get_user(int(stats[0]), ctx=ctx, member=False)
                if user is None:
                    user_info = "**Deleted**"
                else:
                    user_info = f"**{esc(user.name)}#{user.discriminator}**"
            else:
                user_info = (
                    f"**{esc(user.name)}#{user.discriminator}** ({user.mention})"
                )

            leaderboard += f"{i+1}. {user_info} - {int(stats[1])}\n"

        start = int(database.hget(f"race.data:{ctx.channel.id}", "start"))
        elapsed = str(datetime.timedelta(seconds=round(time.time()) - start))

        embed.add_field(name="Options", value=self._get_options(ctx), inline=False)
        embed.add_field(
            name="Stats", value=f"**Race Duration:** `{elapsed}`", inline=False
        )
        embed.add_field(name="Leaderboard", value=leaderboard, inline=False)

        if database.zscore(database_key, str(ctx.author.id)) is not None:
            placement = int(database.zrevrank(database_key, str(ctx.author.id))) + 1
            embed.add_field(name="You:", value=f"You are #{placement}.", inline=False)
        else:
            embed.add_field(name="You:", value="You haven't answered any correctly.")

        await ctx.send(embed=embed)

    async def stop_race(self, ctx):
        first = database.zrevrange(f"race.scores:{ctx.channel.id}", 0, 0, True)[0]
        if ctx.guild is not None:
            user = await fetch_get_user(int(first[0]), ctx=ctx, member=True)
        else:
            user = None

        if user is None:
            user = await fetch_get_user(int(first[0]), ctx=ctx, member=False)
            if user is None:
                user_info = "Deleted"
            else:
                user_info = f"{esc(user.name)}#{user.discriminator}"
        else:
            user_info = f"{esc(user.name)}#{user.discriminator} ({user.mention})"

        await ctx.send(
            f"**Congratulations, {user_info}!**\n"
            + f"You have won the race by correctly identifying `{int(first[1])}` {config.options['id_type']}. "
            + "*Way to go!*"
        )

        database.hset(f"race.data:{ctx.channel.id}", "stop", round(time.time()))

        await self._send_stats(ctx, "**Race stopped.**")
        database.delete(f"race.data:{ctx.channel.id}")
        database.delete(f"race.scores:{ctx.channel.id}")

    @commands.group(
        brief=f"- Base race command. Use '{config.options['prefixes'][0]}help race' for more info.",
        help="- Base race command\n"
        + f"Races allow you to compete with others to see who can ID {config.options['id_type']} first. "
        + "Starting a race will automatically run "
        + f"'{config.options['prefixes'][0]}pic' after every check. "
        + f"You will still need to use '{config.options['prefixes'][0]}check' to check your answer. "
        + "Races are channel-specific, and anyone in that channel can play."
        + f"Races end when a player is the first to correctly ID a set amount of {config.options['id_type']}. (default 10)",
    )
    @commands.guild_only()
    async def race(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Invalid subcommand passed.**\n*Valid Subcommands:* `start, view, stop`"
            )

    @race.command(
        brief="- Starts race",
        help=f"""- Starts race.
        Arguments passed will become the default arguments to '{config.options['prefixes'][0]}pic', but some can be manually overwritten during use.
        Arguments can be passed in any order.""",
        aliases=["st"],
        usage=f"[bw] [state]{' [group]' if config.options['id_groups'] else ''} [amount to win (default 10)]",
    )
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.channel))
    async def start(self, ctx, *, args_str: str = ""):
        logger.info("command: start race")

        if not str(ctx.channel.name).startswith("racing"):
            logger.info("not race channel")
            await ctx.send(
                "**Sorry, racing is not available in this channel.**\n"
                + "*Set the channel name to start with `racing` to enable it.*"
            )
            return

        if database.exists(f"race.data:{ctx.channel.id}"):
            logger.info("already race")
            await ctx.send(
                f"**There is already a race in session.** *View stats with `{config.options['prefixes'][0]}race view`*"
            )
            return

        args = set(args_str.strip().split(" "))
        args.discard("")
        logger.info(f"args: {args}")

        group_args = set()
        state_args = set()
        bw = ""
        strict = ""
        limit = None
        for arg in args:
            arg = arg.lower()
            if arg == "bw":
                bw = "bw"
            elif arg == "strict":
                strict = "strict"
            elif arg in all_categories:
                group_args.add(dealias_group(arg))
            elif arg.upper() in states.keys():
                state_args.add(arg.upper())
            else:
                if not limit:
                    try:
                        limit = int(arg)
                        continue
                    except ValueError:
                        pass
                await ctx.send(f"**Invalid argument provided**: `{arg}`")
                return
        group = " ".join(group_args).strip()
        state = " ".join(state_args).strip()
        limit = limit if limit else 10

        if limit > 1000000:
            await ctx.send("**Sorry, the maximum amount to win is 1 million.**")
            limit = 1000000

        logger.info(f"bw: {bw}; group: {group}; state: {state}; limit: {limit}")

        database.hset(
            f"race.data:{ctx.channel.id}",
            mapping={
                "start": round(time.time()),
                "stop": 0,
                "limit": limit,
                "state": state,
                "bw": bw,
                "group": group,
                "strict": strict,
            },
        )

        database.zadd(f"race.scores:{ctx.channel.id}", {str(ctx.author.id): 0})
        await ctx.send(
            f"**Race started with options:**\n{self._get_options(ctx)}"
        )

        logger.info("clearing previous item")
        database.hset(f"channel:{ctx.channel.id}", "item", "")
        database.hset(f"channel:{ctx.channel.id}", "answered", "1")

        logger.info("auto sending next item")
        media = self.bot.get_cog("Media")
        await media.send_pic(ctx, group, state, bw)

    @race.command(
        brief="- Views race",
        help="- Views race.\n"
        + f"Races allow you to compete with your friends to ID {config.options['id_type']} first.",
    )
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.channel))
    async def view(self, ctx):
        logger.info("command: view race")

        if database.exists(f"race.data:{ctx.channel.id}"):
            await self._send_stats(ctx, "**Race In Progress**")
        else:
            await ctx.send(
                f"**There is no race in session.** *You can start one with `{config.options['prefixes'][0]}race start`*"
            )

    @race.command(help="- Stops race", aliases=["stp", "end"])
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.channel))
    async def stop(self, ctx):
        logger.info("command: stop race")

        if database.exists(f"race.data:{ctx.channel.id}"):
            await self.stop_race(ctx)
        else:
            await ctx.send(
                f"**There is no race in session.** *You can start one with `{config.options['prefixes'][0]}race start`*"
            )


def setup(bot):
    bot.add_cog(Race(bot))
