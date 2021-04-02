# media.py | commands for getting images
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

import random
import string
from typing import Union

from discord.ext import commands

import sciolyid.config as config
from sciolyid.core import send_image
from sciolyid.data import (
    GenericError,
    all_categories,
    database,
    dealias_group,
    logger,
    states,
)
from sciolyid.data_functions import item_setup, session_increment
from sciolyid.functions import (
    CustomCooldown,
    build_id_list,
    check_state_role,
)

IMAGE_MESSAGE = (
    f"*Here you go!* \n**Use `{config.options['prefixes'][0]}pic` again to get a new image of the same {config.options['id_type'][:-1]}, "
    + f"or `{config.options['prefixes'][0]}skip` to get a new {config.options['id_type'][:-1]}."
    + f"Use `{config.options['prefixes'][0]}check [guess]` to check your answer. "
    + f"Use `{config.options['prefixes'][0]}hint` for a hint.**"
)


class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def error_handle(self, ctx, group_str: str, state_str: str, bw: bool, retries):
        """Return a function to pass to send_pic() as on_error."""

        async def inner(error):
            nonlocal retries

            # skip current item
            database.hset(f"channel:{ctx.channel.id}", "item", "")
            database.hset(f"channel:{ctx.channel.id}", "answered", "1")

            if retries >= 2:  # only retry twice
                await ctx.send("**Too many retries.**\n*Please try again.*")
                return

            if isinstance(error, GenericError) and error.code == 100:
                retries += 1
                await ctx.send("**Retrying...**")
                await self.send_pic(ctx, group_str, state_str, bw, retries)
            else:
                await ctx.send("*Please try again.*")

        return inner

    @staticmethod
    def increment_item_frequency(ctx, item):
        item_setup(ctx, item)
        database.zincrby("frequency.item:global", 1, string.capwords(item))
        database.zincrby("frequency.item.refresh:global", 1, string.capwords(item))

    async def send_pic(
        self, ctx, group_str: str, state_str: str, bw: Union[bool, str] = False, retries=0
    ):
        if isinstance(bw, str):
            bw = bw == "bw"

        logger.info(
            f"{config.options['id_type'][:-1]}: "
            + database.hget(f"channel:{ctx.channel.id}", "item").decode("utf-8")
        )

        answered = int(database.hget(f"channel:{ctx.channel.id}", "answered"))
        logger.info(f"answered: {answered}")
        # check to see if previous item was answered
        if answered:  # if yes, give a new item
            session_increment(ctx, "total", 1)

            if config.options["id_groups"]:
                await ctx.send(
                    f"**Recognized arguments:** *Black & White*: `{bw}`, "
                    + f"**{config.options['category_name']}**: `{'None' if group_str == '' else group_str}`, "
                    + f"**Detected State**: `{'None' if state_str == '' else state_str}`"
                )
            else:
                await ctx.send(f"**Recognized arguments:** *Black & White*: `{bw}`")

            choices = build_id_list(group_str, state_str)

            if not choices:
                logger.info(f"no {config.options['id_type']} for taxon/state")
                await ctx.send(
                    f"**Sorry, no {config.options['id_type']} could be found for the taxon/state combo."
                    + "**\n*Please try again*"
                )
                return

            current_item = random.choice(choices)
            self.increment_item_frequency(ctx, current_item)

            prevI = database.hget(f"channel:{ctx.channel.id}", "prevI").decode("utf-8")
            while current_item == prevI and len(choices) > 1:
                current_item = random.choice(choices)
            database.hset(f"channel:{ctx.channel.id}", "prevI", str(current_item))
            database.hset(f"channel:{ctx.channel.id}", "item", str(current_item))
            logger.info("currentItem: " + str(current_item))
            database.hset(f"channel:{ctx.channel.id}", "answered", "0")
            await send_image(
                ctx,
                current_item,
                on_error=self.error_handle(ctx, group_str, state_str, bw, retries),
                message=IMAGE_MESSAGE,
                bw=bw,
            )
        else:  # if no, give the same item
            await send_image(
                ctx,
                database.hget(f"channel:{ctx.channel.id}", "item").decode("utf-8"),
                on_error=self.error_handle(ctx, group_str, state_str, bw, retries),
                message=IMAGE_MESSAGE,
                bw=bw,
            )

    @staticmethod
    async def parse(ctx, args_str: str):
        """Parse arguments for options."""

        args = set(args_str.strip().split(" "))
        args.discard("")

        logger.info(f"args: {args}")

        if not database.exists(f"race.data:{ctx.channel.id}"):
            group_args = set()
            state_args = set()
            for arg in args:
                arg = arg.lower()
                if arg == "bw":
                    continue
                if arg in all_categories:
                    group_args.add(dealias_group(arg))
                elif arg.upper() in states.keys():
                    state_args.add(arg.upper())
                else:
                    await ctx.send(f"**Invalid argument provided**: `{arg}`")
                    return None
            group = " ".join(group_args).strip()

            if database.exists(f"session.data:{ctx.author.id}"):
                logger.info("session parameters")

                if group_args:
                    current_groups = set(
                        database.hget(f"session.data:{ctx.author.id}", "group")
                        .decode("utf-8")
                        .split(" ")
                    )
                    logger.info(f"toggle groups: {group_args}")
                    logger.info(f"current groups: {current_groups}")
                    group_args.symmetric_difference_update(current_groups)
                    group_args.discard("")
                    logger.info(f"new groups: {group_args}")
                    group = " ".join(group_args).strip()
                else:
                    group = database.hget(
                        f"session.data:{ctx.author.id}", "group"
                    ).decode("utf-8")

                chosen_state = (
                    database.hget(f"session.data:{ctx.author.id}", "state")
                    .decode("utf-8")
                    .split(" ")
                )
                if chosen_state[0] == "":
                    chosen_state = []
                if not chosen_state:
                    logger.info("no session lists")
                    chosen_state = check_state_role(ctx)

                session_bw = (
                    database.hget(f"session.data:{ctx.author.id}", "bw").decode("utf-8")
                    == "bw"
                )
                bw = not session_bw if "bw" in args else session_bw
            else:
                chosen_state = check_state_role(ctx)
                bw = "bw" in args

            if state_args:
                logger.info(f"toggle states: {state_args}")
                logger.info(f"current states: {chosen_state}")
                state_args.symmetric_difference_update(set(chosen_state))
                state_args.discard("")
                logger.info(f"new states: {state_args}")
                state = " ".join(state_args).strip()
            else:
                state = " ".join(chosen_state).strip()

        else:
            logger.info("race parameters")

            race_bw = (
                database.hget(f"race.data:{ctx.channel.id}", "bw").decode("utf-8")
                == "bw"
            )
            bw = not race_bw if "bw" in args else race_bw

            group = database.hget(f"race.data:{ctx.channel.id}", "group").decode(
                "utf-8"
            )
            state = database.hget(f"race.data:{ctx.channel.id}", "state").decode(
                "utf-8"
            )

        logger.info(f"args: bw: {bw}; group: {group}; state: {state}")

        return (bw, group, state)

    # Pic command - no args
    # help text
    @commands.command(
        help="- Sends a random image for you to ID",
        aliases=["p", config.options["id_type"][:-1], config.options["short_id_type"]],
    )
    # 5 second cooldown
    @commands.check(CustomCooldown(5.0, bucket=commands.BucketType.channel))
    async def pic(self, ctx, *, args_str: str = ""):
        logger.info("command: pic")
        logger.info(f"args: {args_str}")

        data = await self.parse(ctx, args_str)
        if not data:
            return
        bw, group, state = data

        await self.send_pic(ctx, group, state, bw=bw)


def setup(bot):
    bot.add_cog(Media(bot))
