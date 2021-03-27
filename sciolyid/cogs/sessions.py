# sessions.py | commands for sessions
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

import sciolyid.config as config
from sciolyid.data import all_categories, database, dealias_group, logger, states
from sciolyid.functions import CustomCooldown, check_state_role


class Sessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _get_options(ctx):
        bw, state, group, wiki, strict = database.hmget(
            f"session.data:{ctx.author.id}", ["bw", "state", "group", "wiki", "strict"]
        )
        options = (
            f"**Black & White:** {bw==b'bw'}\n"
            + (
                f"**{config.options['category_name']}:** {group.decode('utf-8') if group else 'None'}\n"
                if config.options["id_groups"]
                else ""
            )
            + f"**Alternate List:** {state.decode('utf-8') if state else 'None'}\n"
            + f"**Wiki Embeds**: {wiki==b'wiki'}\n"
            + f"**Strict Spelling**: {strict==b'strict'}"
        )

        return options

    @staticmethod
    def _get_stats(ctx):
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
            f"**Duration:** `{elapsed}`\n"
            + f"**# Correct:** {correct}\n"
            + f"**# Incorrect:** {incorrect}\n"
            + f"**Total:** {total}\n"
            + f"**Accuracy:** {accuracy}%\n"
        )
        return stats

    async def _send_stats(self, ctx, preamble):
        database_key = f"session.incorrect:{ctx.author.id}"

        embed = discord.Embed(
            type="rich", colour=discord.Color.blurple(), title=preamble
        )
        embed.set_author(name=config.options["bot_signature"])

        if database.zcard(database_key) != 0:
            leaderboard_list = database.zrevrangebyscore(
                database_key, "+inf", "-inf", 0, 5, True
            )
            leaderboard = ""

            for i, stats in enumerate(leaderboard_list):
                leaderboard += (
                    f"{i+1}. **{stats[0].decode('utf-8')}** - {int(stats[1])}\n"
                )
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
        help="- Base session command\nSessions will record your activity for an amount of time and "
        + "will give you stats on how your performance and "
        + "also set global variables such as black and white"
        + (", specific categories, " if config.options["id_groups"] else "")
        + "or alternate lists.",
        aliases=["ses", "sesh"],
    )
    async def session(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Invalid subcommand passed.**\n*Valid Subcommands:* `start, view, stop`"
            )

    # starts session
    @session.command(
        brief="- Starts session",
        help="- Starts session.\n"
        + f"Arguments passed will become the default arguments to '{config.options['prefixes'][0]}{config.options['id_type'][:-1]}', "
        + "but can be manually overwritten during use.\n"
        + f"These settings can be changed at any time with '{config.options['prefixes'][0]}session edit', "
        + "and arguments can be passed in any order.\n",
        aliases=["st"],
        usage=(f"[bw] [state]{' [category]' if config.options['id_groups'] else ''}"),
    )
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.user))
    async def start(self, ctx, *args):
        logger.info("command: start session")

        if database.exists(f"session.data:{ctx.author.id}"):
            logger.info("already session")
            await ctx.send(
                f"**There is already a session running.** *Change settings/view stats with `{config.options['prefixes'][0]}session edit`*"
            )
            return

        logger.info(f"args: {args}")

        # parse args
        group_args = set()
        state_args = set()
        bw = ""
        strict = ""
        wiki = ""
        for arg in set(args):
            arg = arg.lower()
            if arg == "bw":
                bw = "bw"
            elif arg == "wiki":
                wiki = "wiki"
            elif arg == "strict":
                strict = "strict"
            elif arg in all_categories:
                group_args.add(dealias_group(arg))
            elif arg.upper() in states.keys():
                state_args.add(arg.upper())
            else:
                await ctx.send(f"**Invalid argument provided**: `{arg}`")
                return

        if state_args:
            state = " ".join(state_args).strip()
        else:
            state = " ".join(check_state_role(ctx))

        if group_args and config.options["id_groups"]:
            group = " ".join(group_args).strip()
        else:
            group = ""

        logger.info(f"adding bw: {bw}; group: {group}; state: {state}; wiki: {wiki}; strict: {strict}")

        database.hset(
            f"session.data:{ctx.author.id}",
            mapping={
                "start": round(time.time()),
                "stop": 0,
                "correct": 0,
                "incorrect": 0,
                "total": 0,
                "bw": bw,
                "state": state,
                "group": group,
                "wiki": wiki,
                "strict": strict,
            },
        )
        await ctx.send(f"**Session started with options:**\n{self._get_options(ctx)}")

    # views session
    @session.command(
        brief="- Views session",
        help="- Views session\nSessions will record your activity for an amount of time and "
        + "will give you stats on how your performance and "
        + "also set global variables such as black and white"
        + (", specific categories, " if config.options["id_groups"] else "")
        + "or alternate lists.",
        aliases=["view"],
        usage=(f"[bw] [state]{' [category]' if config.options['id_groups'] else ''}"),
    )
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.user))
    async def edit(self, ctx, *args):
        logger.info("command: view session")

        if not database.exists(f"session.data:{ctx.author.id}"):
            await ctx.send(
                f"**There is no session running.** *You can start one with `{config.options['prefixes'][0]}session start`*"
            )
            return

        logger.info(f"args: {args}")

        # parse args
        group_args = set()
        state_args = set()
        for arg in set(args):
            arg = arg.lower()
            if arg == "bw":
                if not database.hget(f"session.data:{ctx.author.id}", "bw"):
                    logger.info("adding bw")
                    database.hset(f"session.data:{ctx.author.id}", "bw", "bw")
                else:
                    logger.info("removing bw")
                    database.hset(f"session.data:{ctx.author.id}", "bw", "")
            elif arg == "wiki":
                if database.hget(f"session.data:{ctx.author.id}", "wiki"):
                    logger.info("disabling wiki embeds")
                    database.hset(f"session.data:{ctx.author.id}", "wiki", "")
                else:
                    logger.info("enabling wiki embeds")
                    database.hset(f"session.data:{ctx.author.id}", "wiki", "wiki")
            elif arg == "strict":
                if database.hget(f"session.data:{ctx.author.id}", "strict"):
                    logger.info("disabling strict spelling")
                    database.hset(f"session.data:{ctx.author.id}", "strict", "")
                else:
                    logger.info("enabling strict spelling")
                    database.hset(
                        f"session.data:{ctx.author.id}", "strict", "strict"
                    )
            elif arg in all_categories:
                group_args.add(dealias_group(arg))
            elif arg.upper() in states.keys():
                state_args.add(arg.upper())
            else:
                await ctx.send(f"**Invalid argument provided**: `{arg}`")
                return

        if state_args:
            current_states = set(
                database.hget(f"session.data:{ctx.author.id}", "state")
                .decode("utf-8")
                .split(" ")
            )
            logger.info(f"toggle states: {state_args}")
            logger.info(f"current states: {current_states}")
            state_args.symmetric_difference_update(current_states)
            state_args.discard("")
            logger.info(f"new states: {state_args}")
            database.hset(
                f"session.data:{ctx.author.id}",
                "state",
                " ".join(state_args).strip(),
            )

        if group_args and config.options["id_groups"]:
            current_group = set(
                database.hget(f"session.data:{ctx.author.id}", "group")
                .decode("utf-8")
                .split(" ")
            )
            logger.info(f"toggle group: {group_args}")
            logger.info(f"current group: {current_group}")
            group_args.symmetric_difference_update(current_group)
            group_args.discard("")
            logger.info(f"new groups: {group_args}")
            database.hset(
                f"session.data:{ctx.author.id}",
                "group",
                " ".join(group_args).strip(),
            )
        await self._send_stats(ctx, "**Session started previously.**\n")


    # stops session
    @session.command(help="- Stops session", aliases=["stp", "end"])
    @commands.check(CustomCooldown(3.0, bucket=commands.BucketType.user))
    async def stop(self, ctx):
        logger.info("command: stop session")

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
