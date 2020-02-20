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

from discord.ext import commands

import sciolyid.config as config
from sciolyid.core import send_image
from sciolyid.data import database, id_list, logger, groups
from sciolyid.functions import channel_setup, error_skip, user_setup, build_id_list

ARG_MESSAGE = f"**Recongnized arguments:** *{config.options['category_name']}*: `"+"{category}`"

IMAGE_MESSAGE = (
    f"*Here you go!* \n**Use `{config.options['prefixes'][0]}pic` again to get a new image of the same {config.options['id_type']}, " +
    f"or `{config.options['prefixes'][0]}skip` to get a new {config.options['id_type']}. Use `{config.options['prefixes'][0]}check [guess]` to check your answer. " +
    f"Use `{config.options['prefixes'][0]}hint` for a hint.**"
)

class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_pic_(self, ctx, args):

        logger.info(f"{config.options['id_type']}: " + str(database.hget(f"channel:{str(ctx.channel.id)}", "item"))[2:-1])

        answered = int(database.hget(f"channel:{str(ctx.channel.id)}", "answered"))
        logger.info(f"answered: {answered}")
        # check to see if previous item was answered
        if answered:  # if yes, give a new item
            if config.options["id_groups"]:
                build = build_id_list(args)
                choices = build[0]
                await ctx.send(ARG_MESSAGE.format(category=build[1]))
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
            await send_image(ctx, currentItem, on_error=error_skip, message=IMAGE_MESSAGE)
        else:  # if no, give the same item
            await send_image(
                ctx,
                str(database.hget(f"channel:{str(ctx.channel.id)}", "item"))[2:-1],
                on_error=error_skip,
                message=IMAGE_MESSAGE
            )


    # Pic command - no args
    # help text
    @commands.command(help='- Sends a random image for you to ID', aliases=["p"])
    # 5 second cooldown
    @commands.cooldown(1, 5.0, type=commands.BucketType.channel)
    async def pic(self, ctx, *, args_str: str = ""):
        logger.info("command: pic")

        await channel_setup(ctx)
        await user_setup(ctx)

        if not config.options["id_groups"]:
            args_str = ""

        await self.send_pic_(ctx, args_str)


def setup(bot):
    bot.add_cog(Media(bot))
