# media.py | commands for getting images
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

import sciolyid.config as config
from discord.ext import commands
from sciolyid.core import send_image
from sciolyid.data import database, groups, id_list, logger
from sciolyid.functions import build_id_list, channel_setup, error_skip, user_setup

IMAGE_MESSAGE = (
    f"*Here you go!* \n**Use `{config.options['prefixes'][0]}pic` again to get a new image of the same {config.options['id_type']}, "
    + f"or `{config.options['prefixes'][0]}skip` to get a new {config.options['id_type']}. Use `{config.options['prefixes'][0]}check [guess]` to check your answer. "
    + f"Use `{config.options['prefixes'][0]}hint` for a hint.**"
)


class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_pic_(self, ctx, group_str: str, bw: bool = False):

        logger.info(
            f"{config.options['id_type']}: "
            + str(database.hget(f"channel:{str(ctx.channel.id)}", "item"))[2:-1]
        )

        answered = int(database.hget(f"channel:{str(ctx.channel.id)}", "answered"))
        logger.info(f"answered: {answered}")
        # check to see if previous item was answered
        if answered:  # if yes, give a new item
            if config.options["id_groups"]:
                build = build_id_list(group_str)
                choices = build[0]
            else:
                choices = id_list

            currentItem = random.choice(choices)
            prevB = str(database.hget(f"channel:{str(ctx.channel.id)}", "prevI"))[2:-1]
            while currentItem == prevB:
                currentItem = random.choice(choices)
            database.hset(f"channel:{str(ctx.channel.id)}", "prevI", str(currentItem))
            database.hset(f"channel:{str(ctx.channel.id)}", "item", str(currentItem))
            logger.info("currentItem: " + str(currentItem))
            database.hset(f"channel:{str(ctx.channel.id)}", "answered", "0")
            await send_image(
                ctx, currentItem, on_error=error_skip, message=IMAGE_MESSAGE, bw=bw
            )
        else:  # if no, give the same item
            await send_image(
                ctx,
                str(database.hget(f"channel:{str(ctx.channel.id)}", "item"))[2:-1],
                on_error=error_skip,
                message=IMAGE_MESSAGE,
                bw=bw,
            )

    # Pic command - no args
    # help text
    @commands.command(
        help="- Sends a random image for you to ID",
        aliases=["p", config.options["id_type"], config.options["id_type"][0]],
    )
    # 5 second cooldown
    @commands.cooldown(1, 5.0, type=commands.BucketType.channel)
    async def pic(self, ctx, *, args_str: str = ""):
        logger.info("command: pic")

        await channel_setup(ctx)
        await user_setup(ctx)

        args = args_str.split(" ")
        logger.info(f"args: {args}")

        bw = "bw" in args
        group_args = set(groups.keys()).intersection({arg.lower() for arg in args})
        if group_args:
            group = " ".join(group_args).strip()
        else:
            group = ""

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

        await self.send_pic_(ctx, group, bw)


def setup(bot):
    bot.add_cog(Media(bot))
