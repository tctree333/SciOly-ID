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

from discord.ext import commands

import sciolyid.config as config
from sciolyid.core import send_image
from sciolyid.data import (
    GenericError,
    all_categories,
    database,
    dealias_group,
    id_list,
    logger,
)
from sciolyid.functions import (
    CustomCooldown,
    build_id_list,
    item_setup,
    session_increment,
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

    def error_handle(self, ctx, group_str: str, bw: bool, retries):
        """Return a function to pass to send_pic() as on_error."""

        async def inner(error):
            nonlocal retries

            # skip current bird
            database.hset(f"channel:{ctx.channel.id}", "item", "")
            database.hset(f"channel:{ctx.channel.id}", "answered", "1")

            if retries >= 2:  # only retry twice
                await ctx.send("**Too many retries.**\n*Please try again.*")
                return

            if isinstance(error, GenericError) and error.code == 100:
                retries += 1
                await ctx.send("**Retrying...**")
                await self.send_pic(ctx, group_str, bw, retries)
            else:
                await ctx.send("*Please try again.*")

        return inner

    @staticmethod
    def increment_item_frequency(ctx, item):
        item_setup(ctx, item)
        database.zincrby("frequency.item:global", 1, string.capwords(item))

    async def send_pic(self, ctx, group_str: str, bw: bool = False, retries=0):

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
                build = build_id_list(group_str)
                choices = build[0]
            else:
                choices = id_list

            current_item = random.choice(choices)
            self.increment_item_frequency(ctx, current_item)

            prevI = database.hget(f"channel:{ctx.channel.id}", "prevI").decode("utf-8")
            while current_item == prevI:
                current_item = random.choice(choices)
            database.hset(f"channel:{ctx.channel.id}", "prevI", str(current_item))
            database.hset(f"channel:{ctx.channel.id}", "item", str(current_item))
            logger.info("currentItem: " + str(current_item))
            database.hset(f"channel:{ctx.channel.id}", "answered", "0")
            await send_image(
                ctx,
                current_item,
                on_error=self.error_handle(ctx, group_str, bw, retries),
                message=IMAGE_MESSAGE,
                bw=bw,
            )
        else:  # if no, give the same item
            await send_image(
                ctx,
                database.hget(f"channel:{ctx.channel.id}", "item").decode("utf-8"),
                on_error=self.error_handle(ctx, group_str, bw, retries),
                message=IMAGE_MESSAGE,
                bw=bw,
            )

    # Pic command - no args
    # help text
    @commands.command(
        help="- Sends a random image for you to ID",
        aliases=["p", config.options["id_type"][:-1], config.options["short_id_type"]],
    )
    # 5 second cooldown
    @commands.check(CustomCooldown(5.0, bucket=commands.BucketType.channel))
    async def pic(self, ctx, *args):
        logger.info("command: pic")

        logger.info(f"args: {args}")

        # parse args
        bw = False
        toggle_groups = []
        for arg in set(args):
            arg = arg.lower()
            if arg == "bw":
                bw = True
            elif arg in all_categories:
                toggle_groups.append(dealias_group(arg))
            else:
                await ctx.send(f"**Invalid argument provided**: `{arg}`")
                return

        logger.info(f"group_args: {toggle_groups}")
        if toggle_groups:
            group = " ".join(toggle_groups).strip()
        else:
            group = ""

        if database.exists(f"session.data:{ctx.author.id}"):
            logger.info("session parameters")
            # handle group args
            if toggle_groups:
                current_groups = (
                    database.hget(f"session.data:{ctx.author.id}", "group")
                    .decode("utf-8")
                    .split(" ")
                )
                add_groups = []
                logger.info(f"toggle group: {toggle_groups}")
                logger.info(f"current group: {current_groups}")
                for o in set(toggle_groups).symmetric_difference(set(current_groups)):
                    add_groups.append(o)
                logger.info(f"adding groups: {add_groups}")
                group = " ".join(add_groups).strip()
            else:
                group = database.hget(f"session.data:{ctx.author.id}", "group").decode(
                    "utf-8"
                )

            if database.hget(f"session.data:{ctx.author.id}", "bw").decode("utf-8"):
                bw = not bw

        if database.exists(f"race.data:{ctx.channel.id}"):
            logger.info("race parameters")

            if database.hget(f"race.data:{ctx.channel.id}", "bw").decode("utf-8"):
                bw = not bw

        if not config.options["id_groups"]:
            group = ""

        logger.info(f"args: bw: {bw}; group: {group}")
        if (
            int(database.hget(f"channel:{ctx.channel.id}", "answered"))
            and config.options["id_groups"]
        ):
            await ctx.send(
                f"**Recognized arguments:** *Black & White*: `{bw}`, "
                + f"*{config.options['category_name']}*: `{'None' if group == '' else group}`"
            )
        else:
            await ctx.send(f"**Recognized arguments:** *Black & White*: `{bw}`")

        await self.send_pic(ctx, group, bw)


def setup(bot):
    bot.add_cog(Media(bot))
