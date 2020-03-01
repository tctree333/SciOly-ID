# sessions.py | commands for sessions
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

import datetime
import time

import discord
from discord.ext import commands

import sciolyid.config as config
from sciolyid.data import database, logger, groups
from sciolyid.functions import channel_setup, user_setup

class Sessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_options(self, ctx):
        bw, group = database.hmget(f"session.data:{ctx.author.id}", ["bw", "group"])
        options = f"**Black & White:** {bw==b'bw'}" + (
            f"\n**{config.options['category_name']}:** {group.decode('utf-8') if group else 'None'}"
            if config.options["id_groups"] else ""
        )
        return options

    def _get_stats(self, ctx):
        start, correct, incorrect, total = map(
            int,
            database.hmget(
                f"session.data:{ctx.author.id}",
                ["start", "correct", "incorrect", "total"],
            ),
        )
        elapsed = str(datetime.timedelta(seconds=round(time.time()) - start))
        try:
            accuracy = round(100 * (correct / (correct + incorrect)), 2)
        except ZeroDivisionError:
            accuracy = 0

        stats = (
            f"**Duration:** `{elapsed}`\n" + f"**# Correct:** {correct}\n" +
            f"**# Incorrect:** {incorrect}\n" + f"**Total:** {total}\n" + f"**Accuracy:** {accuracy}%\n"
        )
        return stats

    async def _send_stats(self, ctx, preamble):
        database_key = f"session.incorrect:{ctx.author.id}"

        embed = discord.Embed(type="rich", colour=discord.Color.blurple(), title=preamble)
        embed.set_author(name=config.options["bot_signature"])

        if database.zcard(database_key) != 0:
            leaderboard_list = database.zrevrangebyscore(database_key, "+inf", "-inf", 0, 5, True)
            leaderboard = ""

            for i, stats in enumerate(leaderboard_list):
                leaderboard += (f"{i+1}. **{stats[0].decode('utf-8')}** - {int(stats[1])}\n")
        else:
            logger.info(f"no items in {database_key}")
            leaderboard = f"**There are no missed {config.options['id_type']}.**"

        embed.add_field(name="Options", value=self._get_options(ctx), inline=False)
        embed.add_field(name="Stats", value=self._get_stats(ctx), inline=False)
        embed.add_field(
            name=f"Top Missed {config.options['id_type'].title()}",
            value=leaderboard,
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.group(
        brief=f"- Base session command. Use '{config.options['prefixes'][0]}help session' for more info.",
        help="- Base session command\nSessions will record your activity for an amount of time and " +
        "will give you stats on how your performance and " +
        "also set global variables such as black and white" +
        (" or specific categories." if config.options["id_groups"] else "."),
        aliases=["ses", "sesh"],
    )
    async def session(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("**Invalid subcommand passed.**\n*Valid Subcommands:* `start, view, stop`")

    # starts session
    @session.command(
        brief="- Starts session",
        help="- Starts session.\n" +
        f"Arguments passed will become the default arguments to '{config.options['prefixes'][0]}{config.options['id_type'][:-1]}', "
        + "but can be manually overwritten during use.\n" +
        f"These settings can be changed at any time with '{config.options['prefixes'][0]}session edit', " +
        "and arguments can be passed in any order.\n",
        aliases=["st"],
        usage=("[bw] [category]" if config.options["id_groups"] else "[bw]"),
    )
    @commands.cooldown(1, 3.0, type=commands.BucketType.user)
    async def start(self, ctx, *, args_str: str = ""):
        logger.info("command: start session")

        await channel_setup(ctx)
        await user_setup(ctx)

        if database.exists(f"session.data:{ctx.author.id}"):
            logger.info("already session")
            await ctx.send(
                f"**There is already a session running.** *Change settings/view stats with `{config.options['prefixes'][0]}session edit`*"
            )
            return
        else:
            args = args_str.split(" ")
            logger.info(f"args: {args}")
            if "bw" in args:
                bw = "bw"
            else:
                bw = ""
            group_args = []
            for category in set(
                list(groups.keys()) +
                [item for group in groups.keys() for item in config.options["category_aliases"][group]]
            ).intersection({arg.lower()
                            for arg in args}):
                if category not in groups.keys():
                    category = next(
                        key for key, value in config.options["category_aliases"].items() if category in value
                    )
                group_args.append(category)
            if group_args and config.options["id_groups"]:
                group = " ".join(group_args).strip()
            else:
                group = ""
            logger.info(f"adding bw: {bw}; group: {group}")

            database.hmset(
                f"session.data:{ctx.author.id}",
                {
                    "start": round(time.time()),
                    "stop": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "total": 0,
                    "bw": bw,
                    "group": group,
                },
            )
            await ctx.send(f"**Session started with options:**\n{self._get_options(ctx)}")

    # views session
    @session.command(
        brief="- Views session",
        help="- Views session\nSessions will record your activity for an amount of time and " +
        "will give you stats on how your performance and " +
        "also set global variables such as black and white" +
        (" or specific categories." if config.options["id_groups"] else "."),
        aliases=["view"],
        usage=("[bw] [category]" if config.options["id_groups"] else "[bw]"),
    )
    @commands.cooldown(1, 3.0, type=commands.BucketType.user)
    async def edit(self, ctx, *, args_str: str = ""):
        logger.info("command: view session")

        await channel_setup(ctx)
        await user_setup(ctx)

        if database.exists(f"session.data:{ctx.author.id}"):
            args = args_str.split(" ")
            logger.info(f"args: {args}")
            if "bw" in args:
                if not database.hget(f"session.data:{ctx.author.id}", "bw"):
                    logger.info("adding bw")
                    database.hset(f"session.data:{ctx.author.id}", "bw", "bw")
                else:
                    logger.info("removing bw")
                    database.hset(f"session.data:{ctx.author.id}", "bw", "")
            group_args = []
            for category in set(
                list(groups.keys()) +
                [item for group in groups.keys() for item in config.options["category_aliases"][group]]
            ).intersection({arg.lower()
                            for arg in args}):
                if category not in groups.keys():
                    category = next(
                        key for key, value in config.options["category_aliases"].items() if category in value
                    )
                group_args.append(category)
            if group_args and config.options["id_groups"]:
                toggle_group = list(group_args)
                current_group = (
                    database.hget(f"session.data:{ctx.author.id}", "group").decode("utf-8").split(" ")
                )
                add_group = []
                logger.info(f"toggle group: {toggle_group}")
                logger.info(f"current group: {current_group}")
                for o in set(toggle_group).symmetric_difference(set(current_group)):
                    add_group.append(o)
                logger.info(f"adding groups: {add_group}")
                database.hset(
                    f"session.data:{ctx.author.id}",
                    "group",
                    " ".join(add_group).strip(),
                )
            await self._send_stats(ctx, f"**Session started previously.**\n")
        else:
            await ctx.send(
                f"**There is no session running.** *You can start one with `{config.options['prefixes'][0]}session start`*"
            )

    # stops session
    @session.command(help="- Stops session", aliases=["stp", "end"])
    @commands.cooldown(1, 3.0, type=commands.BucketType.user)
    async def stop(self, ctx):
        logger.info("command: stop session")

        await channel_setup(ctx)
        await user_setup(ctx)

        if database.exists(f"session.data:{ctx.author.id}"):
            database.hset(f"session.data:{ctx.author.id}", "stop", round(time.time()))

            await self._send_stats(ctx, "**Session stopped.**\n")
            database.delete(f"session.data:{ctx.author.id}")
            database.delete(f"session.incorrect:{ctx.author.id}")
        else:
            await ctx.send(
                f"**There is no session running.** *You can start one with `{config.options['prefixes'][0]}session start`*"
            )

def setup(bot):
    bot.add_cog(Sessions(bot))
