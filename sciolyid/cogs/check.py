# check.py | commands to check answers
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

import discord
from discord.ext import commands

from sciolyid.data import database, get_wiki_url, logger, get_aliases
from sciolyid.functions import channel_setup, score_increment, spellcheck_list, user_setup


class Check(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Check command - argument is the guess
    @commands.command(help='- Checks your answer.', usage="guess", aliases=["guess", "c"])
    @commands.cooldown(1, 3.0, type=commands.BucketType.user)
    async def check(self, ctx, *, arg):
        logger.info("command: check")

        await channel_setup(ctx)
        await user_setup(ctx)

        currentItem = str(database.hget(f"channel:{str(ctx.channel.id)}", "item"))[2:-1]
        if currentItem == "":  # no image
            await ctx.send("You must ask for a image first!")
        else:  # if there is a image, it checks answer
            logger.info("currentItem: " + str(currentItem.lower().replace("-", " ")))
            logger.info("args: " + str(arg.lower().replace("-", " ")))

            if spellcheck_list(arg, get_aliases(currentItem.lower())) is True:
                logger.info("correct")

                database.hset(f"channel:{str(ctx.channel.id)}", "item", "")
                database.hset(f"channel:{str(ctx.channel.id)}", "answered", "1")

                
                database.zincrby("streak:global", 1, str(ctx.author.id))
                # check if streak is greater than max, if so, increases max
                if database.zscore("streak:global", str(ctx.author.id))> database.zscore("streak.max:global", str(ctx.author.id)):
                    database.zadd("streak.max:global", {str(ctx.author.id): database.zscore("streak:global", str(ctx.author.id))})

                await ctx.send("Correct! Good job!")
                url = get_wiki_url(currentItem)
                await ctx.send(url)
                score_increment(ctx, 1)

            else:
                logger.info("incorrect")
                
                database.zadd("streak:global", {str(ctx.author.id): 0})

                database.hset(f"channel:{str(ctx.channel.id)}", "item", "")
                database.hset(f"channel:{str(ctx.channel.id)}", "answered", "1")
                await ctx.send("Sorry, the image was actually " + currentItem.lower() + ".")
                url = get_wiki_url(currentItem)
                await ctx.send(url)


def setup(bot):
    bot.add_cog(Check(bot))
